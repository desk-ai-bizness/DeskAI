"""ElevenLabs Scribe v2 Realtime transcription adapter."""

from __future__ import annotations

import io
import wave
from typing import TYPE_CHECKING, Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from deskai.adapters.transcription.elevenlabs_config import ElevenLabsConfig
from deskai.domain.transcription.exceptions import (
    ProviderSessionError,
    ProviderUnavailableError,
)
from deskai.ports.transcription_provider import TranscriptionProvider
from deskai.shared.logging import get_logger

if TYPE_CHECKING:
    from deskai.adapters.storage.s3_client import S3Client

logger = get_logger()

_STATE_READY = "ready"
_STATE_STREAMING = "streaming"
_STATE_CLOSED = "closed"
_PCM_FALLBACK_SAMPLE_RATE = 16000
_PCM_FALLBACK_CHANNELS = 1
_PCM_SAMPLE_WIDTH_BYTES = 2
_AUDIO_CHUNKS_PREFIX = "audio-chunks"


class _SessionEntry:
    """Internal mutable state for a single provider session."""

    __slots__ = (
        "session_id",
        "language",
        "state",
        "audio_buffer",
        "chunk_count",
        "cached_transcript",
    )

    def __init__(self, session_id: str, language: str) -> None:
        self.session_id = session_id
        self.language = language
        self.state = _STATE_READY
        self.audio_buffer = bytearray()
        self.chunk_count: int = 0
        self.cached_transcript: dict[str, Any] | None = None


class ElevenLabsScribeProvider(TranscriptionProvider):
    """ElevenLabs Scribe v2 adapter implementing TranscriptionProvider.

    When an ``s3_client`` is provided, audio chunks are persisted to S3
    instead of being buffered in-memory.  This makes the provider
    resilient to Lambda horizontal scaling where each invocation may
    land on a different execution environment.

    Without ``s3_client`` (backward-compatible mode), chunks are
    accumulated in an in-memory ``bytearray`` as before.
    """

    def __init__(self, config: ElevenLabsConfig, s3_client: S3Client | None = None) -> None:
        self._config = config
        self._s3 = s3_client
        self._sessions: dict[str, _SessionEntry] = {}

    # ------------------------------------------------------------------
    # Port interface
    # ------------------------------------------------------------------

    def start_realtime_session(self, session_id: str, language: str) -> dict[str, Any]:
        if session_id in self._sessions:
            raise ProviderSessionError(f"Session '{session_id}' already exists")

        entry = _SessionEntry(session_id=session_id, language=language)
        self._sessions[session_id] = entry

        logger.info(
            "elevenlabs_session_started",
            extra={
                "session_id": session_id,
                "language": language,
            },
        )

        return {
            "session_id": session_id,
            "provider": "elevenlabs",
            "model": self._config.model,
            "language": language,
            "state": entry.state,
        }

    def send_audio_chunk(self, session_id: str, audio_data: bytes) -> None:
        entry = self._get_or_create_session(session_id)

        if entry.state == _STATE_CLOSED:
            raise ProviderSessionError(f"Session '{session_id}' is already closed")
        if not audio_data:
            raise ProviderSessionError("Audio data must not be empty")

        if self._s3 is not None:
            key = f"{_AUDIO_CHUNKS_PREFIX}/{session_id}/{entry.chunk_count:06d}.bin"
            self._s3.put_bytes(key, audio_data, "application/octet-stream")
            entry.chunk_count += 1
        else:
            entry.audio_buffer.extend(audio_data)

        entry.state = _STATE_STREAMING

    def finish_realtime_session(self, session_id: str) -> dict[str, Any]:
        entry = self._get_or_create_session(session_id)

        if entry.state == _STATE_CLOSED:
            raise ProviderSessionError(f"Session '{session_id}' is already closed")

        if self._s3 is not None:
            audio_size = self._read_s3_audio_size(session_id)
        else:
            audio_size = len(entry.audio_buffer)

        entry.state = _STATE_CLOSED

        logger.info(
            "elevenlabs_session_closed",
            extra={
                "session_id": session_id,
                "audio_bytes": audio_size,
            },
        )

        return {
            "session_id": session_id,
            "state": _STATE_CLOSED,
            "audio_bytes_received": audio_size,
        }

    def fetch_final_transcript(self, session_id: str) -> dict[str, Any]:
        entry = self._require_session(session_id)

        if entry.state != _STATE_CLOSED:
            raise ProviderSessionError(
                f"Session '{session_id}' must be closed before fetching transcript"
            )

        if entry.cached_transcript is not None:
            return entry.cached_transcript

        result = self._post_audio_to_api(entry)
        entry.cached_transcript = result
        return result

    def get_session_state(self, session_id: str) -> str:
        entry = self._require_session(session_id)
        return entry.state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_session(self, session_id: str) -> _SessionEntry:
        entry = self._sessions.get(session_id)
        if entry is None:
            raise ProviderSessionError(f"Unknown session '{session_id}'")
        return entry

    def _get_or_create_session(self, session_id: str) -> _SessionEntry:
        """Return existing session or auto-create one when S3 storage is enabled.

        When running on Lambda with S3-backed storage, a different container
        may receive ``send_audio_chunk`` or ``finish_realtime_session``
        without having seen ``start_realtime_session``.  In that case we
        create a lightweight session entry so chunks can still be persisted.
        Without S3, fall back to the strict ``_require_session`` behavior.
        """
        entry = self._sessions.get(session_id)
        if entry is not None:
            return entry
        if self._s3 is not None:
            entry = _SessionEntry(session_id=session_id, language="pt")
            self._sessions[session_id] = entry
            logger.info(
                "elevenlabs_session_auto_created",
                extra={"session_id": session_id},
            )
            return entry
        raise ProviderSessionError(f"Unknown session '{session_id}'")

    def _reassemble_s3_audio(self, session_id: str) -> bytes:
        """Read and concatenate all audio chunks from S3 for *session_id*."""
        prefix = f"{_AUDIO_CHUNKS_PREFIX}/{session_id}/"
        keys = self._s3.list_keys(prefix)
        buffer = bytearray()
        for key in keys:
            chunk = self._s3.get_bytes(key)
            if chunk is not None:
                buffer.extend(chunk)
        logger.info(
            "elevenlabs_s3_audio_reassembled",
            extra={
                "session_id": session_id,
                "chunk_count": len(keys),
                "total_bytes": len(buffer),
            },
        )
        return bytes(buffer)

    def _read_s3_audio_size(self, session_id: str) -> int:
        """Calculate total audio bytes from S3 chunks without full reassembly."""
        prefix = f"{_AUDIO_CHUNKS_PREFIX}/{session_id}/"
        keys = self._s3.list_keys(prefix)
        total = 0
        for key in keys:
            chunk = self._s3.get_bytes(key)
            if chunk is not None:
                total += len(chunk)
        return total

    def _post_audio_to_api(self, entry: _SessionEntry) -> dict[str, Any]:
        """Send buffered audio to the ElevenLabs HTTP endpoint.

        Uses tenacity retry for transient failures (timeout,
        connection errors, 5xx responses).
        """
        try:
            return self._post_with_retry(entry)
        except httpx.TimeoutException as exc:
            raise ProviderUnavailableError(f"ElevenLabs API timed out: {exc}") from exc
        except httpx.ConnectError as exc:
            raise ProviderUnavailableError(f"Cannot connect to ElevenLabs: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            response_excerpt = exc.response.text[:300].strip()
            if status >= 500:
                message = f"ElevenLabs server error ({status})"
                if response_excerpt:
                    message = f"{message}: {response_excerpt}"
                raise ProviderUnavailableError(message) from exc
            message = f"ElevenLabs API error ({status})"
            if response_excerpt:
                message = f"{message}: {response_excerpt}"
            raise ProviderSessionError(message) from exc

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )
    def _post_with_retry(self, entry: _SessionEntry) -> dict[str, Any]:
        """Perform the actual HTTP POST with retry."""
        if self._s3 is not None:
            original_audio = self._reassemble_s3_audio(entry.session_id)
        else:
            original_audio = bytes(entry.audio_buffer)
        filename, audio_bytes, content_type = self._prepare_audio_payload(
            original_audio, entry.session_id
        )

        response = httpx.post(
            f"{self._config.http_endpoint}",
            headers={"xi-api-key": self._config.api_key},
            files={
                "file": (
                    filename,
                    audio_bytes,
                    content_type,
                ),
            },
            data={
                "model_id": self._config.model,
                "language_code": entry.language,
            },
            timeout=self._config.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def _prepare_audio_payload(self, audio_bytes: bytes, session_id: str) -> tuple[str, bytes, str]:
        """Prepare a supported audio file payload for ElevenLabs.

        If bytes already look like a known container (wav/ogg/mp3/flac/webm/mp4),
        keep them as-is. Otherwise, assume raw PCM16 mono and wrap as WAV.
        """
        if self._looks_like_wav(audio_bytes):
            return "audio.wav", audio_bytes, "audio/wav"
        if audio_bytes.startswith(b"OggS"):
            return "audio.ogg", audio_bytes, "audio/ogg"
        if audio_bytes.startswith(b"fLaC"):
            return "audio.flac", audio_bytes, "audio/flac"
        if audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
            return "audio.webm", audio_bytes, "audio/webm"
        if audio_bytes.startswith(b"ID3") or audio_bytes.startswith(b"\xff\xfb"):
            return "audio.mp3", audio_bytes, "audio/mpeg"
        if len(audio_bytes) > 8 and audio_bytes[4:8] == b"ftyp":
            return "audio.mp4", audio_bytes, "audio/mp4"

        wrapped = self._wrap_pcm16_as_wav(audio_bytes)
        logger.info(
            "elevenlabs_audio_wrapped_as_wav",
            extra={
                "session_id": session_id,
                "input_bytes": len(audio_bytes),
                "output_bytes": len(wrapped),
            },
        )
        return "audio.wav", wrapped, "audio/wav"

    @staticmethod
    def _looks_like_wav(audio_bytes: bytes) -> bool:
        return (
            len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE"
        )

    @staticmethod
    def _wrap_pcm16_as_wav(audio_bytes: bytes) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(_PCM_FALLBACK_CHANNELS)
            wav_file.setsampwidth(_PCM_SAMPLE_WIDTH_BYTES)
            wav_file.setframerate(_PCM_FALLBACK_SAMPLE_RATE)
            wav_file.writeframes(audio_bytes)
        return buffer.getvalue()
