"""End a real-time consultation session."""

from dataclasses import dataclass, replace
from datetime import datetime

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import SessionNotFoundError
from deskai.domain.session.services import SessionService
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.event_publisher import EventPublisher
from deskai.ports.session_repository import SessionRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()

_POST_SESSION_STATUSES = frozenset(
    {
        ConsultationStatus.IN_PROCESSING,
        ConsultationStatus.DRAFT_GENERATED,
        ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
        ConsultationStatus.FINALIZED,
    }
)


@dataclass(frozen=True)
class EndSessionUseCase:
    """Validate inputs, end session, transition consultation to IN_PROCESSING."""

    consultation_repo: ConsultationRepository
    session_repo: SessionRepository
    audit_repo: AuditRepository
    event_publisher: EventPublisher

    def execute(
        self,
        consultation_id: str,
        doctor_id: str,
        clinic_id: str,
    ) -> Session:
        logger.info(
            "session_end_requested",
            extra=log_context(
                consultation_id=consultation_id,
                doctor_id=doctor_id,
                clinic_id=clinic_id,
            ),
        )

        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise ConsultationNotFoundError(f"Consultation {consultation_id} not found")

        if consultation.doctor_id != doctor_id:
            raise ConsultationOwnershipError("Requesting doctor does not own this consultation")

        # Idempotency: if already past recording, return the existing session
        if consultation.status in _POST_SESSION_STATUSES:
            existing = self.session_repo.find_active_by_consultation_id(consultation_id)
            if existing is not None:
                logger.info(
                    "session_end_idempotent",
                    extra=log_context(
                        consultation_id=consultation_id,
                        session_id=existing.session_id,
                    ),
                )
                return existing

        session = self.session_repo.find_active_by_consultation_id(consultation_id)
        if session is None:
            raise SessionNotFoundError(f"No active session for consultation {consultation_id}")

        SessionService.validate_session_end(session.state)

        now = utc_now_iso()
        started = datetime.fromisoformat(session.started_at)
        ended = datetime.fromisoformat(now)
        duration = int((ended - started).total_seconds())

        session = replace(
            session,
            state=SessionState.ENDED,
            ended_at=now,
            duration_seconds=duration,
        )

        self.session_repo.update(session)

        logger.info(
            "session_ended",
            extra=log_context(
                session_id=session.session_id,
                consultation_id=consultation_id,
                duration_seconds=duration,
            ),
        )

        consultation = replace(
            consultation,
            status=ConsultationStatus.IN_PROCESSING,
            session_ended_at=now,
            processing_started_at=now,
            updated_at=now,
        )
        self.consultation_repo.save(consultation)

        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.SESSION_ENDED,
                actor_id=doctor_id,
                timestamp=now,
                payload={
                    "session_id": session.session_id,
                    "duration_seconds": duration,
                },
            )
        )

        self.event_publisher.publish(
            "consultation.session.ended",
            {"consultation_id": consultation_id, "clinic_id": clinic_id},
        )

        return session
