"""Port interface for doctor profile persistence."""

from abc import ABC, abstractmethod

from deskai.domain.auth.entities import DoctorProfile


class DoctorRepository(ABC):
    """Abstract doctor profile repository."""

    @abstractmethod
    def find_by_cognito_sub(self, cognito_sub: str) -> DoctorProfile | None:
        """Look up a doctor profile by Cognito user ID."""

    @abstractmethod
    def count_consultations_this_month(self, doctor_id: str) -> int:
        """Count consultations created by this doctor in the current calendar month."""

    @abstractmethod
    def find_created_at(self, doctor_id: str) -> str | None:
        """Return the ISO 8601 account creation timestamp for the doctor, or None."""
