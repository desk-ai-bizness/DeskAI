"""Lazy-initializing wrapper for TranscriptionProvider.

Defers secret loading and provider construction until the first
transcription method is actually called.  This prevents cold-start
failures from blocking unrelated endpoints (auth, patients, etc.)
when the provider secret is temporarily inaccessible.
"""

from collections.abc import Callable

from deskai.domain.transcription.value_objects import (
    FinalTranscript,
    TranscriptionSessionInfo,
)
from deskai.ports.transcription_provider import TranscriptionProvider
from deskai.shared.logging import get_logger

logger = get_logger()


class LazyTranscriptionProvider(TranscriptionProvider):
    """Wraps a factory that produces the real TranscriptionProvider.

    The factory is invoked on the first method call, not at init time.
    If the factory raises, the error propagates to the caller and the
    next call will retry (the failed result is not cached).
    """

    def __init__(self, factory: Callable[[], TranscriptionProvider]) -> None:
        self._factory = factory
        self._delegate: TranscriptionProvider | None = None

    def _get_delegate(self) -> TranscriptionProvider:
        if self._delegate is None:
            logger.info("lazy_transcription_provider_initializing")
            self._delegate = self._factory()
            logger.info("lazy_transcription_provider_ready")
        return self._delegate

    def start_realtime_session(self, session_id: str, language: str) -> TranscriptionSessionInfo:
        return self._get_delegate().start_realtime_session(session_id, language)

    def send_audio_chunk(self, session_id: str, audio_data: bytes) -> None:
        self._get_delegate().send_audio_chunk(session_id, audio_data)

    def finish_realtime_session(self, session_id: str) -> TranscriptionSessionInfo:
        return self._get_delegate().finish_realtime_session(session_id)

    def fetch_final_transcript(self, session_id: str) -> FinalTranscript:
        return self._get_delegate().fetch_final_transcript(session_id)

    def get_session_state(self, session_id: str) -> str:
        return self._get_delegate().get_session_state(session_id)
