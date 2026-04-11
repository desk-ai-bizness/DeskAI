"""Unit tests for the ElevenLabs Scribe v2 transcription provider adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.transcription.elevenlabs_config import ElevenLabsConfig
from deskai.adapters.transcription.elevenlabs_provider import (
    ElevenLabsScribeProvider,
)
from deskai.domain.transcription.exceptions import (
    ProviderSessionError,
    ProviderUnavailableError,
)


def _make_config(**overrides: object) -> ElevenLabsConfig:
    """Build an ElevenLabsConfig with sensible test defaults."""
    defaults = {
        "api_key": "test-api-key-123",
        "ws_endpoint": "wss://api.elevenlabs.io/v1/speech-to-text/ws",
        "model": "scribe_v2",
        "language": "pt",
        "timeout_seconds": 30,
    }
    defaults.update(overrides)
    return ElevenLabsConfig(**defaults)


class StartRealtimeSessionTest(unittest.TestCase):
    """Tests for start_realtime_session."""

    def test_start_session_returns_session_info(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        result = provider.start_realtime_session(session_id="sess-001", language="pt")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["session_id"], "sess-001")
        self.assertEqual(result["provider"], "elevenlabs")
        self.assertEqual(result["model"], "scribe_v2")
        self.assertEqual(result["language"], "pt")
        self.assertIn("state", result)

    def test_start_session_sets_state_to_ready(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        result = provider.start_realtime_session(session_id="sess-002", language="pt")

        self.assertEqual(result["state"], "ready")

    def test_start_session_tracks_session_internally(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        provider.start_realtime_session(session_id="sess-003", language="pt")

        state = provider.get_session_state("sess-003")
        self.assertEqual(state, "ready")

    def test_start_session_uses_config_language_as_default(self) -> None:
        config = _make_config(language="en")
        provider = ElevenLabsScribeProvider(config)

        result = provider.start_realtime_session(session_id="sess-004", language="en")

        self.assertEqual(result["language"], "en")

    def test_start_duplicate_session_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        provider.start_realtime_session(session_id="sess-dup", language="pt")

        with self.assertRaises(ProviderSessionError):
            provider.start_realtime_session(session_id="sess-dup", language="pt")


class SendAudioChunkTest(unittest.TestCase):
    """Tests for send_audio_chunk."""

    def test_send_audio_chunk_buffers_data(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-010", language="pt")

        audio_data = b"\x00\x01\x02\x03" * 100

        # Should not raise
        provider.send_audio_chunk("sess-010", audio_data)

    def test_send_audio_chunk_multiple_times(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-011", language="pt")

        provider.send_audio_chunk("sess-011", b"\x00\x01")
        provider.send_audio_chunk("sess-011", b"\x02\x03")
        provider.send_audio_chunk("sess-011", b"\x04\x05")

        state = provider.get_session_state("sess-011")
        self.assertEqual(state, "streaming")

    def test_send_audio_chunk_unknown_session_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        with self.assertRaises(ProviderSessionError):
            provider.send_audio_chunk("sess-unknown", b"\x00\x01")

    def test_send_audio_chunk_empty_data_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-012", language="pt")

        with self.assertRaises(ProviderSessionError):
            provider.send_audio_chunk("sess-012", b"")

    def test_send_audio_chunk_to_closed_session_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-013", language="pt")
        provider.send_audio_chunk("sess-013", b"\x00\x01")
        provider.finish_realtime_session("sess-013")

        with self.assertRaises(ProviderSessionError):
            provider.send_audio_chunk("sess-013", b"\x02\x03")


class FinishRealtimeSessionTest(unittest.TestCase):
    """Tests for finish_realtime_session."""

    def test_finish_session_returns_raw_response(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-020", language="pt")
        provider.send_audio_chunk("sess-020", b"\x00\x01\x02")

        result = provider.finish_realtime_session("sess-020")

        self.assertIsInstance(result, dict)
        self.assertIn("session_id", result)
        self.assertEqual(result["session_id"], "sess-020")
        self.assertIn("state", result)

    def test_finish_session_sets_state_to_closed(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-021", language="pt")
        provider.send_audio_chunk("sess-021", b"\x00\x01")

        provider.finish_realtime_session("sess-021")

        state = provider.get_session_state("sess-021")
        self.assertEqual(state, "closed")

    def test_finish_session_stores_audio_buffer(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-022", language="pt")
        provider.send_audio_chunk("sess-022", b"\x00\x01")
        provider.send_audio_chunk("sess-022", b"\x02\x03")

        result = provider.finish_realtime_session("sess-022")

        self.assertIn("audio_bytes_received", result)
        self.assertEqual(result["audio_bytes_received"], 4)

    def test_finish_unknown_session_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        with self.assertRaises(ProviderSessionError):
            provider.finish_realtime_session("sess-missing")

    def test_finish_already_closed_session_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-023", language="pt")
        provider.send_audio_chunk("sess-023", b"\x00\x01")
        provider.finish_realtime_session("sess-023")

        with self.assertRaises(ProviderSessionError):
            provider.finish_realtime_session("sess-023")

    def test_finish_session_without_audio_succeeds(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-024", language="pt")

        result = provider.finish_realtime_session("sess-024")

        self.assertEqual(result["audio_bytes_received"], 0)
        self.assertEqual(result["state"], "closed")


class FetchFinalTranscriptTest(unittest.TestCase):
    """Tests for fetch_final_transcript."""

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_fetch_final_transcript_calls_api(self, mock_httpx: MagicMock) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-030", language="pt")
        provider.send_audio_chunk("sess-030", b"\x00\x01\x02\x03")
        provider.finish_realtime_session("sess-030")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language_code": "pt",
            "text": "Doutor eu sinto dor de cabeca",
            "words": [
                {
                    "text": "Doutor",
                    "start": 0.0,
                    "end": 0.5,
                    "speaker_id": "speaker_0",
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        result = provider.fetch_final_transcript("sess-030")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["text"], "Doutor eu sinto dor de cabeca")
        self.assertEqual(result["language_code"], "pt")
        mock_httpx.post.assert_called_once()

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_fetch_final_transcript_sends_audio_buffer(self, mock_httpx: MagicMock) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-031", language="pt")
        provider.send_audio_chunk("sess-031", b"\x00\x01")
        provider.send_audio_chunk("sess-031", b"\x02\x03")
        provider.finish_realtime_session("sess-031")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language_code": "pt",
            "text": "Ola",
            "words": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        provider.fetch_final_transcript("sess-031")

        call_kwargs = mock_httpx.post.call_args
        self.assertIn("files", call_kwargs[1])

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_fetch_final_transcript_wraps_raw_pcm_into_wav(self, mock_httpx: MagicMock) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-031b", language="pt")
        provider.send_audio_chunk("sess-031b", b"\x01\x02\x03\x04")
        provider.finish_realtime_session("sess-031b")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language_code": "pt",
            "text": "ok",
            "words": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        provider.fetch_final_transcript("sess-031b")

        call_kwargs = mock_httpx.post.call_args[1]
        filename, uploaded_bytes, content_type = call_kwargs["files"]["file"]
        self.assertEqual(filename, "audio.wav")
        self.assertEqual(content_type, "audio/wav")
        self.assertTrue(uploaded_bytes.startswith(b"RIFF"))
        self.assertEqual(uploaded_bytes[8:12], b"WAVE")

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_fetch_final_transcript_keeps_ogg_payload_when_detected(self, mock_httpx: MagicMock) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-031c", language="pt")
        provider.send_audio_chunk("sess-031c", b"OggS\x00\x01\x02\x03")
        provider.finish_realtime_session("sess-031c")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language_code": "pt",
            "text": "ok",
            "words": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        provider.fetch_final_transcript("sess-031c")

        call_kwargs = mock_httpx.post.call_args[1]
        filename, uploaded_bytes, content_type = call_kwargs["files"]["file"]
        self.assertEqual(filename, "audio.ogg")
        self.assertEqual(content_type, "audio/ogg")
        self.assertEqual(uploaded_bytes, b"OggS\x00\x01\x02\x03")

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_fetch_final_transcript_includes_auth_header(self, mock_httpx: MagicMock) -> None:
        config = _make_config(api_key="my-secret-key")
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-032", language="pt")
        provider.send_audio_chunk("sess-032", b"\x00")
        provider.finish_realtime_session("sess-032")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language_code": "pt",
            "text": "Oi",
            "words": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        provider.fetch_final_transcript("sess-032")

        call_kwargs = mock_httpx.post.call_args
        headers = call_kwargs[1].get("headers", {})
        self.assertEqual(headers.get("xi-api-key"), "my-secret-key")

    def test_fetch_final_transcript_unknown_session_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        with self.assertRaises(ProviderSessionError):
            provider.fetch_final_transcript("sess-missing")

    def test_fetch_final_transcript_not_closed_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-033", language="pt")

        with self.assertRaises(ProviderSessionError):
            provider.fetch_final_transcript("sess-033")

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_fetch_final_transcript_caches_result(self, mock_httpx: MagicMock) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-034", language="pt")
        provider.send_audio_chunk("sess-034", b"\x00")
        provider.finish_realtime_session("sess-034")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language_code": "pt",
            "text": "Cached result",
            "words": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        result1 = provider.fetch_final_transcript("sess-034")
        result2 = provider.fetch_final_transcript("sess-034")

        self.assertEqual(result1, result2)
        # Only called once due to caching
        mock_httpx.post.assert_called_once()


class GetSessionStateTest(unittest.TestCase):
    """Tests for get_session_state."""

    def test_get_state_unknown_session_raises(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)

        with self.assertRaises(ProviderSessionError):
            provider.get_session_state("sess-no-exist")

    def test_get_state_after_start(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-040", language="pt")

        self.assertEqual(provider.get_session_state("sess-040"), "ready")

    def test_get_state_after_audio(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-041", language="pt")
        provider.send_audio_chunk("sess-041", b"\x00")

        self.assertEqual(provider.get_session_state("sess-041"), "streaming")

    def test_get_state_after_close(self) -> None:
        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-042", language="pt")
        provider.send_audio_chunk("sess-042", b"\x00")
        provider.finish_realtime_session("sess-042")

        self.assertEqual(provider.get_session_state("sess-042"), "closed")


class ErrorHandlingTest(unittest.TestCase):
    """Tests for error mapping to domain exceptions."""

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_api_timeout_raises_provider_unavailable(self, mock_httpx: MagicMock) -> None:
        import httpx

        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-050", language="pt")
        provider.send_audio_chunk("sess-050", b"\x00")
        provider.finish_realtime_session("sess-050")

        mock_httpx.post.side_effect = httpx.TimeoutException("connection timed out")
        mock_httpx.TimeoutException = httpx.TimeoutException

        with self.assertRaises(ProviderUnavailableError):
            provider.fetch_final_transcript("sess-050")

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_connection_error_raises_provider_unavailable(self, mock_httpx: MagicMock) -> None:
        import httpx

        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-051", language="pt")
        provider.send_audio_chunk("sess-051", b"\x00")
        provider.finish_realtime_session("sess-051")

        mock_httpx.post.side_effect = httpx.ConnectError("connection refused")
        mock_httpx.ConnectError = httpx.ConnectError
        mock_httpx.TimeoutException = httpx.TimeoutException

        with self.assertRaises(ProviderUnavailableError):
            provider.fetch_final_transcript("sess-051")

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_api_401_raises_provider_session_error(self, mock_httpx: MagicMock) -> None:
        import httpx

        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-052", language="pt")
        provider.send_audio_chunk("sess-052", b"\x00")
        provider.finish_realtime_session("sess-052")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        mock_httpx.post.return_value = mock_response
        mock_httpx.TimeoutException = httpx.TimeoutException
        mock_httpx.ConnectError = httpx.ConnectError
        mock_httpx.HTTPStatusError = httpx.HTTPStatusError

        with self.assertRaises(ProviderSessionError):
            provider.fetch_final_transcript("sess-052")

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_api_500_raises_provider_unavailable(self, mock_httpx: MagicMock) -> None:
        import httpx

        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-053", language="pt")
        provider.send_audio_chunk("sess-053", b"\x00")
        provider.finish_realtime_session("sess-053")

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_httpx.post.return_value = mock_response
        mock_httpx.TimeoutException = httpx.TimeoutException
        mock_httpx.ConnectError = httpx.ConnectError
        mock_httpx.HTTPStatusError = httpx.HTTPStatusError

        with self.assertRaises(ProviderUnavailableError):
            provider.fetch_final_transcript("sess-053")


class RetryOnTransientFailureTest(unittest.TestCase):
    """Tests for tenacity retry on transient failures."""

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_retries_on_timeout_then_succeeds(self, mock_httpx: MagicMock) -> None:
        import httpx

        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-060", language="pt")
        provider.send_audio_chunk("sess-060", b"\x00")
        provider.finish_realtime_session("sess-060")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "language_code": "pt",
            "text": "Retry success",
            "words": [],
        }
        mock_response.raise_for_status = MagicMock()

        mock_httpx.TimeoutException = httpx.TimeoutException
        mock_httpx.ConnectError = httpx.ConnectError
        mock_httpx.HTTPStatusError = httpx.HTTPStatusError
        mock_httpx.post.side_effect = [
            httpx.TimeoutException("timeout"),
            mock_response,
        ]

        result = provider.fetch_final_transcript("sess-060")

        self.assertEqual(result["text"], "Retry success")
        self.assertEqual(mock_httpx.post.call_count, 2)

    @patch("deskai.adapters.transcription.elevenlabs_provider.httpx")
    def test_retries_exhausted_raises_provider_unavailable(self, mock_httpx: MagicMock) -> None:
        import httpx

        config = _make_config()
        provider = ElevenLabsScribeProvider(config)
        provider.start_realtime_session(session_id="sess-061", language="pt")
        provider.send_audio_chunk("sess-061", b"\x00")
        provider.finish_realtime_session("sess-061")

        mock_httpx.TimeoutException = httpx.TimeoutException
        mock_httpx.ConnectError = httpx.ConnectError
        mock_httpx.HTTPStatusError = httpx.HTTPStatusError
        mock_httpx.post.side_effect = httpx.TimeoutException("timeout")

        with self.assertRaises(ProviderUnavailableError):
            provider.fetch_final_transcript("sess-061")

        # Should have tried 3 times (initial + 2 retries)
        self.assertEqual(mock_httpx.post.call_count, 3)


if __name__ == "__main__":
    unittest.main()
