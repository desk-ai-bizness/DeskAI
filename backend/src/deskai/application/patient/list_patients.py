"""List patients in a clinic."""

from dataclasses import dataclass

from deskai.domain.patient.entities import Patient
from deskai.ports.patient_repository import PatientRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


@dataclass(frozen=True)
class ListPatientsUseCase:
    """Query patients by clinic with optional search filter."""

    patient_repo: PatientRepository

    def execute(
        self,
        clinic_id: str,
        search_term: str = "",
    ) -> list[Patient]:
        result = self.patient_repo.find_by_clinic(clinic_id, search_term)
        logger.debug(
            "patients_listed",
            extra=log_context(
                clinic_id=clinic_id,
                count=len(result),
                search_present=bool(search_term),
            ),
        )
        return result
