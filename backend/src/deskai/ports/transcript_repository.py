"""Port interface for transcript persistence."""

from abc import ABC, abstractmethod


class TranscriptRepository(ABC):
    """Persistence contract for transcription artifacts."""

    @abstractmethod
    def save_raw_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
        raw_response: dict,
    ) -> None:
        """Persist the raw provider response as-is."""

    @abstractmethod
    def save_normalized_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
        normalized: dict,
    ) -> None:
        """Persist the normalized transcript."""

    @abstractmethod
    def get_normalized_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
    ) -> dict | None:
        """Load the normalized transcript, or None if not found."""
