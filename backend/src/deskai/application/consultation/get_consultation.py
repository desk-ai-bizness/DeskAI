"""Retrieve a single consultation by ID."""

from dataclasses import dataclass

from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.entities import Consultation
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.ports.consultation_repository import ConsultationRepository


@dataclass(frozen=True)
class GetConsultationUseCase:
    """Load a consultation or raise not-found, enforcing doctor ownership."""

    consultation_repo: ConsultationRepository

    def execute(
        self,
        auth_context: AuthContext,
        consultation_id: str,
        clinic_id: str,
    ) -> Consultation:
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if not consultation:
            raise ConsultationNotFoundError(
                f"Consultation {consultation_id} not found"
            )

        if consultation.doctor_id != auth_context.doctor_id:
            raise ConsultationOwnershipError(
                f"Doctor {auth_context.doctor_id} does not own consultation {consultation_id}"
            )

        return consultation
