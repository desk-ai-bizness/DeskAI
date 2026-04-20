"""Issue a single-use transcription token for client-side realtime scribe."""

from dataclasses import dataclass
from typing import Any

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.session.exceptions import InvalidSessionStateError
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.transcription_token_provider import TranscriptionTokenProvider
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


@dataclass(frozen=True)
class IssueTranscriptionTokenUseCase:
    """Validate ownership and state, then issue a single-use token."""

    consultation_repo: ConsultationRepository
    transcription_token_provider: TranscriptionTokenProvider
    audit_repo: AuditRepository

    def execute(
        self,
        consultation_id: str,
        doctor_id: str,
        clinic_id: str,
    ) -> dict[str, Any]:
        logger.info(
            "transcription_token_requested",
            extra=log_context(consultation_id=consultation_id, doctor_id=doctor_id),
        )

        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise ConsultationNotFoundError(f"Consultation {consultation_id} not found")

        if consultation.doctor_id != doctor_id:
            raise ConsultationOwnershipError(
                "Requesting doctor does not own this consultation"
            )

        if consultation.status != ConsultationStatus.RECORDING:
            raise InvalidSessionStateError(
                f"Cannot issue token: consultation is '{consultation.status}', "
                "expected 'recording'"
            )

        token_data = self.transcription_token_provider.create_single_use_token()

        now = utc_now_iso()
        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.PROCESSING_STARTED,
                actor_id=doctor_id,
                timestamp=now,
                payload={"action": "transcription_token_issued"},
            )
        )

        logger.info(
            "transcription_token_issued",
            extra=log_context(consultation_id=consultation_id),
        )

        return token_data
