"""List patients in a clinic."""

from dataclasses import dataclass

from deskai.domain.patient.entities import Patient
from deskai.ports.patient_repository import PatientRepository


@dataclass(frozen=True)
class ListPatientsUseCase:
    """Query patients by clinic with optional search filter."""

    patient_repo: PatientRepository

    def execute(
        self,
        clinic_id: str,
        search_term: str = "",
    ) -> list[Patient]:
        return self.patient_repo.find_by_clinic(clinic_id, search_term)
