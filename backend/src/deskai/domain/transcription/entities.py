"""Transcription domain entities."""

from dataclasses import dataclass
from typing import Any

from deskai.domain.transcription.value_objects import CompletenessStatus, SpeakerSegment
from deskai.shared.errors import DomainValidationError


@dataclass(frozen=True)
class NormalizedTranscript:
    """Immutable entity representing a normalized transcription result."""

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

    def __post_init__(self) -> None:
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not self.provider_name or not self.provider_name.strip():
            raise DomainValidationError("provider_name must be a non-empty string")
        if not self.provider_session_id or not self.provider_session_id.strip():
            raise DomainValidationError("provider_session_id must be a non-empty string")
        if not self.language or not self.language.strip():
            raise DomainValidationError("language must be a non-empty string")
        if not isinstance(self.completeness_status, CompletenessStatus):
            raise DomainValidationError(f"completeness_status must be a CompletenessStatus, got {type(self.completeness_status).__name__}")
