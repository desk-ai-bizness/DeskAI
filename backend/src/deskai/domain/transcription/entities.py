"""Transcription domain entities."""

from dataclasses import dataclass
from typing import Any

from deskai.domain.transcription.value_objects import (
    CompletenessStatus,
    SpeakerSegment,
)


@dataclass
class NormalizedTranscript:
    """Mutable entity representing a normalized transcription result."""

    consultation_id: str
    provider_name: str
    provider_session_id: str
    language: str
    transcript_text: str
    speaker_segments: list[SpeakerSegment]
    timestamps: dict[str, Any] | None = None
    confidence_metadata: dict[str, Any] | None = None
    completeness_status: CompletenessStatus = CompletenessStatus.PENDING
    raw_response_key: str | None = None
    normalized_artifact_key: str | None = None
    created_at: str = ""
    updated_at: str = ""
