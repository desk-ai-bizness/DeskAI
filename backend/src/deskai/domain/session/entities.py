"""Session domain entities."""

from dataclasses import dataclass
from enum import StrEnum


class SessionState(StrEnum):
    """Business states for a real-time consultation session."""

    CONNECTING = "connecting"
    ACTIVE = "active"
    RECORDING = "recording"
    STOPPING = "stopping"
    ENDED = "ended"
    DISCONNECTED = "disconnected"


@dataclass
class Session:
    """Real-time consultation session aggregate."""

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
