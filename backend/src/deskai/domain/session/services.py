"""Session domain services — pure functions for session validation and computation."""

from datetime import datetime, timedelta

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import (
    AudioChunkRejectedError,
    InvalidSessionStateError,
    SessionOwnershipError,
    SessionPauseRejectedError,
)
from deskai.shared.time import utc_now_iso


class SessionService:
    """Pure domain service for session validation logic."""

    @staticmethod
    def validate_transition(current_state: SessionState, target_state: SessionState) -> None:
        """Validate that a session state transition is allowed."""
        from deskai.domain.session.entities import VALID_SESSION_TRANSITIONS

        allowed = VALID_SESSION_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            raise InvalidSessionStateError(
                f"Cannot transition from '{current_state}' to '{target_state}'"
            )

    @staticmethod
    def validate_session_start(
        consultation_status: ConsultationStatus,
        consultation_doctor_id: str,
        requesting_doctor_id: str,
    ) -> None:
        """Validate that a session can be started for a consultation."""
        if consultation_doctor_id != requesting_doctor_id:
            raise SessionOwnershipError("Requesting doctor does not own this consultation")
        if consultation_status != ConsultationStatus.STARTED:
            raise InvalidSessionStateError(
                f"Cannot start session: consultation is '{consultation_status}', expected 'started'"
            )

    @staticmethod
    def validate_audio_chunk(
        session_state: SessionState,
        session_doctor_id: str,
        requesting_doctor_id: str,
    ) -> None:
        """Validate that an audio chunk can be accepted."""
        if session_doctor_id != requesting_doctor_id:
            raise SessionOwnershipError("Requesting doctor does not own this session")
        if session_state not in (SessionState.RECORDING, SessionState.ACTIVE):
            raise AudioChunkRejectedError(f"Cannot accept audio: session is '{session_state}'")

    @staticmethod
    def validate_pause(session_state: SessionState) -> None:
        """Validate that a session can be paused. Must be RECORDING."""
        if session_state != SessionState.RECORDING:
            raise SessionPauseRejectedError(
                f"Cannot pause session: session is '{session_state}', expected 'recording'"
            )

    @staticmethod
    def validate_resume(session_state: SessionState) -> None:
        """Validate that a session can be resumed. Must be PAUSED."""
        if session_state != SessionState.PAUSED:
            raise SessionPauseRejectedError(
                f"Cannot resume session: session is '{session_state}', expected 'paused'"
            )

    @staticmethod
    def validate_session_end(session_state: SessionState) -> None:
        """Validate that a session can be ended."""
        if session_state not in (
            SessionState.RECORDING,
            SessionState.PAUSED,
            SessionState.ACTIVE,
            SessionState.DISCONNECTED,
        ):
            raise InvalidSessionStateError(f"Cannot end session: session is '{session_state}'")

    @staticmethod
    def compute_grace_period_expiry(disconnect_time: str, grace_minutes: int = 5) -> str:
        """Compute the ISO timestamp when the grace period expires."""
        dt = datetime.fromisoformat(disconnect_time)
        expiry = dt + timedelta(minutes=grace_minutes)
        return expiry.isoformat()

    @staticmethod
    def is_grace_period_expired(grace_period_expires_at: str, current_time: str) -> bool:
        """Check whether the grace period has expired."""
        expiry = datetime.fromisoformat(grace_period_expires_at)
        current = datetime.fromisoformat(current_time)
        return current >= expiry

    @staticmethod
    def can_reconnect(session: Session) -> bool:
        """Check whether a session can accept a reconnection."""
        if session.state != SessionState.DISCONNECTED:
            return False
        if session.grace_period_expires_at is None:
            return False
        current = utc_now_iso()
        return not SessionService.is_grace_period_expired(session.grace_period_expires_at, current)
