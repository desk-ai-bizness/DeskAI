"""Port interface for patient persistence."""

from abc import ABC, abstractmethod

from deskai.domain.patient.entities import Patient


class PatientRepository(ABC):
    """Abstract patient repository."""

    @abstractmethod
    def save(self, patient: Patient) -> None:
        """Persist a patient record."""

    @abstractmethod
    def find_by_cpf(self, cpf: str, clinic_id: str) -> Patient | None:
        """Look up a patient by normalized CPF within a clinic."""

    @abstractmethod
    def find_by_id(self, patient_id: str, clinic_id: str) -> Patient | None:
        """Look up a patient by ID within a clinic."""

    @abstractmethod
    def find_by_clinic(
        self, clinic_id: str, search_term: str = ""
    ) -> list[Patient]:
        """List patients in a clinic, optionally filtered by search term."""
