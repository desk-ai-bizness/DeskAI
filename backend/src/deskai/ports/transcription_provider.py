"""Transcription provider adapter contract."""

from abc import ABC, abstractmethod

from deskai.domain.transcription.value_objects import (
    FinalTranscript,
    TranscriptionSessionInfo,
)


class TranscriptionProvider(ABC):
    """Provider contract for real-time transcription."""

    @abstractmethod
    def start_realtime_session(
        self, session_id: str, language: str
    ) -> TranscriptionSessionInfo:
        """Start a provider-side session."""

    @abstractmethod
    def send_audio_chunk(self, session_id: str, audio_data: bytes) -> None:
        """Send one audio chunk to the provider."""

    @abstractmethod
    def finish_realtime_session(
        self, session_id: str
    ) -> TranscriptionSessionInfo:
        """Close session and request transcript finalization."""

    @abstractmethod
    def fetch_final_transcript(self, session_id: str) -> FinalTranscript:
        """Retrieve the final transcript for a closed session."""

    @abstractmethod
    def get_session_state(self, session_id: str) -> str:
        """Return the current provider-side state of a session."""
