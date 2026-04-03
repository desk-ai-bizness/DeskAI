"""Session domain entities."""

from dataclasses import dataclass
from enum import StrEnum

from deskai.shared.errors import DomainValidationError


class SessionState(StrEnum):
    """Business states for a real-time consultation session."""

    CONNECTING = "connecting"
    ACTIVE = "active"
    RECORDING = "recording"
    STOPPING = "stopping"
    ENDED = "ended"
    DISCONNECTED = "disconnected"


VALID_SESSION_TRANSITIONS: dict[SessionState, set[SessionState]] = {
    SessionState.CONNECTING: {SessionState.ACTIVE, SessionState.DISCONNECTED},
    SessionState.ACTIVE: {SessionState.RECORDING, SessionState.STOPPING, SessionState.DISCONNECTED},
    SessionState.RECORDING: {SessionState.STOPPING, SessionState.DISCONNECTED},
    SessionState.STOPPING: {SessionState.ENDED},
    SessionState.ENDED: set(),
    SessionState.DISCONNECTED: {SessionState.ACTIVE, SessionState.ENDED},
}


@dataclass(frozen=True)
class Session:
    """Real-time consultation session aggregate — immutable."""

    session_id: str
    consultation_id: str
    doctor_id: str
    clinic_id: str
    connection_id: str | None = None
    state: SessionState = SessionState.CONNECTING
    started_at: str = ""
    ended_at: str | None = None
    duration_seconds: int = 0
    audio_chunks_received: int = 0
    grace_period_expires_at: str | None = None
    last_activity_at: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id or not self.session_id.strip():
            raise DomainValidationError("session_id must be a non-empty string")
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not self.doctor_id or not self.doctor_id.strip():
            raise DomainValidationError("doctor_id must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not isinstance(self.state, SessionState):
            raise DomainValidationError(f"state must be a SessionState, got {type(self.state).__name__}")
        if self.duration_seconds < 0:
            raise DomainValidationError("duration_seconds must be non-negative")
        if self.audio_chunks_received < 0:
            raise DomainValidationError("audio_chunks_received must be non-negative")
