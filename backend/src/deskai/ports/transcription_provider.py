"""Transcription provider adapter contract."""

from abc import ABC, abstractmethod


class TranscriptionProvider(ABC):
    """Provider contract for real-time transcription."""

    @abstractmethod
    def start_realtime_session(self, session_id: str, language: str) -> dict[str, object]:
        """Start a provider-side session."""

    @abstractmethod
    def send_audio_chunk(self, session_id: str, audio_data: bytes) -> None:
        """Send one audio chunk to the provider."""

    @abstractmethod
    def finish_realtime_session(self, session_id: str) -> dict[str, object]:
        """Close session and request transcript finalization."""
