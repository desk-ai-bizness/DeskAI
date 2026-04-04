"""List consultations for a doctor within a date range."""

from dataclasses import dataclass

from deskai.domain.consultation.entities import Consultation
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


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
        results = self.consultation_repo.find_by_doctor_and_date_range(
            doctor_id, start_date, end_date
        )
        logger.debug(
            "consultations_listed",
            extra=log_context(
                doctor_id=doctor_id,
                start_date=start_date or None,
                end_date=end_date or None,
                count=len(results),
            ),
        )
        return results
