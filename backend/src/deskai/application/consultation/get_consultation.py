"""Retrieve a single consultation by ID."""

from dataclasses import dataclass

from deskai.domain.consultation.entities import Consultation
from deskai.domain.consultation.exceptions import ConsultationNotFoundError
from deskai.ports.consultation_repository import ConsultationRepository


@dataclass(frozen=True)
class GetConsultationUseCase:
    """Load a consultation or raise not-found."""

    consultation_repo: ConsultationRepository

    def execute(self, consultation_id: str, clinic_id: str) -> Consultation:
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if not consultation:
            raise ConsultationNotFoundError(
                f"Consultation {consultation_id} not found"
            )
        return consultation
