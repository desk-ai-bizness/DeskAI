"""Transcription domain value objects."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from deskai.shared.errors import DomainValidationError


class CompletenessStatus(StrEnum):
    """Completeness state of a transcription."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


class TranscriptionLanguage(StrEnum):
    """Supported transcription languages."""

    PT_BR = "pt-BR"


@dataclass(frozen=True)
class SpeakerSegment:
    """Immutable segment of transcribed speech attributed to a speaker."""

    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: float

    def __post_init__(self) -> None:
        if not self.speaker or not self.speaker.strip():
            raise DomainValidationError("speaker must be a non-empty string")
        if self.start_time < 0:
            raise DomainValidationError("start_time must be non-negative")
        if self.end_time < 0:
            raise DomainValidationError("end_time must be non-negative")
        if self.end_time < self.start_time:
            raise DomainValidationError("end_time must be >= start_time")
        if not (0.0 <= self.confidence <= 1.0):
            raise DomainValidationError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class PartialTranscript:
    """Immutable real-time partial transcription update."""

    text: str
    speaker: str
    is_final: bool
    timestamp: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.speaker or not self.speaker.strip():
            raise DomainValidationError("speaker must be a non-empty string")
        if not self.timestamp or not self.timestamp.strip():
            raise DomainValidationError("timestamp must be a non-empty string")
        if not (0.0 <= self.confidence <= 1.0):
            raise DomainValidationError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class TranscriptionSessionInfo:
    """Immutable snapshot of a transcription session's state."""

    session_id: str
    state: str
    provider_name: str
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.session_id or not self.session_id.strip():
            raise DomainValidationError("session_id must be a non-empty string")
        if not self.state or not self.state.strip():
            raise DomainValidationError("state must be a non-empty string")
        if not self.provider_name or not self.provider_name.strip():
            raise DomainValidationError("provider_name must be a non-empty string")


@dataclass(frozen=True)
class FinalTranscript:
    """Immutable final transcription result from a provider."""

    session_id: str
    text: str
    speaker_segments: list[SpeakerSegment]
    language: str
    provider_name: str
    duration_seconds: float = 0.0
    confidence: float = 0.0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.session_id or not self.session_id.strip():
            raise DomainValidationError("session_id must be a non-empty string")
        if not self.language or not self.language.strip():
            raise DomainValidationError("language must be a non-empty string")
        if not self.provider_name or not self.provider_name.strip():
            raise DomainValidationError("provider_name must be a non-empty string")
        if self.duration_seconds < 0:
            raise DomainValidationError("duration_seconds must be non-negative")
        if not (0.0 <= self.confidence <= 1.0):
            raise DomainValidationError("confidence must be between 0.0 and 1.0")
