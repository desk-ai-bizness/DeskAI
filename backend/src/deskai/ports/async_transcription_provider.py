"""Async port for real-time transcription streaming."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from deskai.domain.transcription.value_objects import (
    FinalTranscript,
    PartialTranscript,
    TranscriptionSessionInfo,
)


class AsyncTranscriptionProvider(ABC):
    """Async contract for streaming transcription sessions."""

    @abstractmethod
    async def start_session(
        self, session_id: str, language: str
    ) -> TranscriptionSessionInfo:
        """Open a streaming transcription session."""

    @abstractmethod
    async def send_audio_chunk(
        self, session_id: str, audio_data: bytes
    ) -> None:
        """Push one audio chunk into the session."""

    @abstractmethod
    async def receive_partials(
        self, session_id: str
    ) -> AsyncIterator[PartialTranscript]:
        """Yield partial transcription updates as they arrive."""

    @abstractmethod
    async def finish_session(self, session_id: str) -> FinalTranscript:
        """Close the session and return the final transcript."""

    @abstractmethod
    async def get_session_state(self, session_id: str) -> str:
        """Return the current state of a streaming session."""
