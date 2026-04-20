"""Port interface for transcript segment persistence."""

from abc import ABC, abstractmethod

from deskai.domain.transcription.value_objects import CommittedSegment


class TranscriptSegmentRepository(ABC):
    """Abstract repository for committed transcript segments."""

    @abstractmethod
    def save(self, segment: CommittedSegment) -> None:
        """Persist a single committed segment."""

    @abstractmethod
    def save_batch(self, segments: list[CommittedSegment]) -> None:
        """Persist multiple committed segments."""

    @abstractmethod
    def find_by_consultation(self, consultation_id: str) -> list[CommittedSegment]:
        """Retrieve all segments for a consultation, ordered by timestamp and index."""
