"""Consultation repository port interface."""

from abc import ABC, abstractmethod

from deskai.domain.consultation.entities import Consultation, ConsultationStatus


class ConsultationRepository(ABC):
    """Persistence contract for consultations."""

    @abstractmethod
    def save(self, consultation: Consultation) -> None:
        """Persist a consultation aggregate."""

    @abstractmethod
    def find_by_id(self, consultation_id: str, clinic_id: str) -> Consultation | None:
        """Load a consultation by identifier within a clinic context."""

    @abstractmethod
    def find_by_doctor_and_date_range(
        self, doctor_id: str, start_date: str, end_date: str
    ) -> list[Consultation]:
        """Find consultations for a doctor within a date range."""

    @abstractmethod
    def find_by_patient_for_doctor(
        self, clinic_id: str, patient_id: str, doctor_id: str
    ) -> list[Consultation]:
        """Find a patient's consultations owned by a specific doctor."""

    @abstractmethod
    def update_status(
        self, consultation_id: str, new_status: ConsultationStatus, **kwargs: object
    ) -> None:
        """Update the status of a consultation."""
