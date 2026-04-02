"""List consultations for a doctor within a date range."""

from dataclasses import dataclass

from deskai.domain.consultation.entities import Consultation
from deskai.ports.consultation_repository import ConsultationRepository


@dataclass(frozen=True)
class ListConsultationsUseCase:
    """Query consultations by doctor and optional date range."""

    consultation_repo: ConsultationRepository

    def execute(
        self,
        doctor_id: str,
        start_date: str = "",
        end_date: str = "",
    ) -> list[Consultation]:
        return self.consultation_repo.find_by_doctor_and_date_range(
            doctor_id, start_date, end_date
        )
