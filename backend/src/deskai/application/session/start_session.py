"""Start a real-time consultation session."""

from dataclasses import dataclass, replace

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.services import SessionService
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.session_repository import SessionRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.time import utc_now_iso


@dataclass(frozen=True)
class StartSessionUseCase:
    """Validate inputs, create session, transition consultation to RECORDING."""

    consultation_repo: ConsultationRepository
    session_repo: SessionRepository
    audit_repo: AuditRepository

    def execute(
        self,
        consultation_id: str,
        doctor_id: str,
        clinic_id: str,
    ) -> Session:
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise ConsultationNotFoundError(
                f"Consultation {consultation_id} not found"
            )

        if consultation.doctor_id != doctor_id:
            raise ConsultationOwnershipError(
                "Requesting doctor does not own this consultation"
            )

        # Idempotency: if already recording, return the existing session
        if consultation.status == ConsultationStatus.RECORDING:
            existing = self.session_repo.find_active_by_consultation_id(
                consultation_id
            )
            if existing is not None:
                return existing

        SessionService.validate_session_start(
            consultation.status, consultation.doctor_id, doctor_id
        )

        now = utc_now_iso()
        session = Session(
            session_id=new_uuid(),
            consultation_id=consultation_id,
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            state=SessionState.ACTIVE,
            started_at=now,
        )

        self.session_repo.save(session)

        consultation = replace(
            consultation,
            status=ConsultationStatus.RECORDING,
            session_started_at=now,
            updated_at=now,
        )
        self.consultation_repo.save(consultation)

        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.SESSION_STARTED,
                actor_id=doctor_id,
                timestamp=now,
                payload={"session_id": session.session_id},
            )
        )

        return session
