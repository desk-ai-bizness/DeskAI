"""Session domain value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioChunk:
    """Immutable audio data chunk received during a session."""

    chunk_index: int
    audio_data: bytes
    timestamp: str
    session_id: str


@dataclass(frozen=True)
class ConnectionInfo:
    """Immutable WebSocket connection metadata."""

    connection_id: str
    session_id: str
    doctor_id: str
    clinic_id: str
    connected_at: str
