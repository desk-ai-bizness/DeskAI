"""Session domain value objects."""

from dataclasses import dataclass

from deskai.shared.errors import DomainValidationError


@dataclass(frozen=True)
class AudioChunk:
    """Immutable audio data chunk received during a session."""

    chunk_index: int
    audio_data: bytes
    timestamp: str
    session_id: str

    def __post_init__(self) -> None:
        if self.chunk_index < 0:
            raise DomainValidationError("chunk_index must be non-negative")
        if not self.timestamp or not self.timestamp.strip():
            raise DomainValidationError("timestamp must be a non-empty string")
        if not self.session_id or not self.session_id.strip():
            raise DomainValidationError("session_id must be a non-empty string")


@dataclass(frozen=True)
class ConnectionInfo:
    """Immutable WebSocket connection metadata."""

    connection_id: str
    session_id: str
    doctor_id: str
    clinic_id: str
    connected_at: str

    def __post_init__(self) -> None:
        if not self.connection_id or not self.connection_id.strip():
            raise DomainValidationError("connection_id must be a non-empty string")
        if self.session_id is None:
            raise DomainValidationError("session_id must be a string, got None")
        if not self.doctor_id or not self.doctor_id.strip():
            raise DomainValidationError("doctor_id must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not self.connected_at or not self.connected_at.strip():
            raise DomainValidationError("connected_at must be a non-empty string")
