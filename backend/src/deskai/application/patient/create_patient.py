"""Create a new patient record within a clinic."""

from dataclasses import dataclass

from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.patient.entities import Patient
from deskai.domain.patient.exceptions import PatientValidationError
from deskai.ports.patient_repository import PatientRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


@dataclass(frozen=True)
class CreatePatientUseCase:
    """Validate and persist a new patient."""

    patient_repo: PatientRepository

    def execute(
        self,
        auth_context: AuthContext,
        name: str,
        date_of_birth: str,
    ) -> Patient:
        if not name or not name.strip():
            raise PatientValidationError("Patient name is required.")
        if not date_of_birth:
            raise PatientValidationError("Date of birth is required.")

        patient = Patient(
            patient_id=new_uuid(),
            name=name.strip(),
            date_of_birth=date_of_birth,
            clinic_id=auth_context.clinic_id,
            created_at=utc_now_iso(),
        )
        self.patient_repo.save(patient)
        logger.info(
            "patient_created",
            extra=log_context(patient_id=patient.patient_id, clinic_id=auth_context.clinic_id),
        )
        return patient
