"""Consultation value objects."""

from dataclasses import dataclass
from enum import StrEnum

from deskai.shared.errors import DomainValidationError


class Specialty(StrEnum):
    """Supported consultation specialties."""

    GENERAL_PRACTICE = "general_practice"


class ArtifactType(StrEnum):
    """Types of artifacts produced during a consultation."""

    TRANSCRIPT_RAW = "transcript_raw"
    TRANSCRIPT_NORMALIZED = "transcript_normalized"
    MEDICAL_HISTORY = "medical_history"
    SUMMARY = "summary"
    INSIGHTS = "insights"
    PHYSICIAN_EDITS = "physician_edits"
    FINAL_VERSION = "final_version"
    EXPORT_PDF = "export_pdf"


@dataclass(frozen=True)
class ArtifactPointer:
    """Immutable reference to a stored artifact."""

    artifact_type: ArtifactType
    storage_key: str
    version: str = ""
    is_complete: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_type, ArtifactType):
            raise DomainValidationError(f"artifact_type must be an ArtifactType, got {type(self.artifact_type).__name__}")
        if not self.storage_key or not self.storage_key.strip():
            raise DomainValidationError("storage_key must be a non-empty string")
