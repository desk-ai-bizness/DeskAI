"""Consultation value objects."""

from dataclasses import dataclass
from enum import StrEnum


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
    s3_key: str
    version: str = ""
    is_complete: bool = True
