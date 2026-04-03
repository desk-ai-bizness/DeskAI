"""Transcription domain value objects."""

from dataclasses import dataclass
from enum import StrEnum


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


@dataclass(frozen=True)
class PartialTranscript:
    """Immutable real-time partial transcription update."""

    text: str
    speaker: str
    is_final: bool
    timestamp: str
    confidence: float


@dataclass(frozen=True)
class TranscriptionSessionInfo:
    """Immutable snapshot of a transcription session's state."""

    session_id: str
    state: str
    provider_name: str
    metadata: dict | None = None


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
    metadata: dict | None = None
