"""Consultation repository port interface."""

from abc import ABC, abstractmethod

from deskai.domain.consultation.entities import Consultation


class ConsultationRepository(ABC):
    """Persistence contract for consultations."""

    @abstractmethod
    def save(self, consultation: Consultation) -> None:
        """Persist a consultation aggregate."""

    @abstractmethod
    def find_by_id(self, consultation_id: str) -> Consultation | None:
        """Load a consultation by identifier."""
