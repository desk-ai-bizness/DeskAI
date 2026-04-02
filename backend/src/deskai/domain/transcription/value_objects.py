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
