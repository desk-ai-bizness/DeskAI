"""Resume a paused real-time consultation session."""

from dataclasses import dataclass, replace

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import (
    SessionNotFoundError,
    SessionOwnershipError,
)
from deskai.domain.session.services import SessionService
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.session_repository import SessionRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


@dataclass(frozen=True)
class ResumeSessionUseCase:
    """Validate state, transition session back to RECORDING, and audit."""

    session_repo: SessionRepository
    audit_repo: AuditRepository

    def execute(self, consultation_id: str, doctor_id: str) -> Session:
        session = self.session_repo.find_active_by_consultation_id(consultation_id)
        if session is None:
            raise SessionNotFoundError(
                f"No active session for consultation {consultation_id}"
            )

        if session.doctor_id != doctor_id:
            raise SessionOwnershipError(
                "Requesting doctor does not own this session"
            )

        SessionService.validate_resume(session.state)

        now = utc_now_iso()
        session = replace(
            session,
            state=SessionState.RECORDING,
            last_activity_at=now,
        )
        self.session_repo.update(session)

        logger.info(
            "session_resumed",
            extra=log_context(
                session_id=session.session_id,
                consultation_id=consultation_id,
            ),
        )

        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.SESSION_RESUMED,
                actor_id=doctor_id,
                timestamp=now,
                payload={"session_id": session.session_id},
            )
        )

        return session
