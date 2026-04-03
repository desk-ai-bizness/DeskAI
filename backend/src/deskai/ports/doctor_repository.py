"""Port interface for doctor profile persistence."""

from abc import ABC, abstractmethod

from deskai.domain.auth.entities import DoctorProfile


class DoctorRepository(ABC):
    """Abstract doctor profile repository."""

    @abstractmethod
    def find_by_identity_provider_id(
        self, identity_provider_id: str
    ) -> DoctorProfile | None:
        """Look up a doctor profile by identity provider user ID."""

    @abstractmethod
    def count_consultations_this_month(self, doctor_id: str) -> int:
        """Count consultations created by this doctor in the current calendar month."""
