"""S3 artifact key strategy for consultation artifacts."""

from deskai.domain.consultation.value_objects import ArtifactType

_ARTIFACT_PATHS: dict[ArtifactType, str] = {
    ArtifactType.TRANSCRIPT_RAW: "transcripts/raw.json",
    ArtifactType.TRANSCRIPT_NORMALIZED: "transcripts/normalized.json",
    ArtifactType.MEDICAL_HISTORY: "ai/medical_history.json",
    ArtifactType.SUMMARY: "ai/summary.json",
    ArtifactType.INSIGHTS: "ai/insights.json",
    ArtifactType.PHYSICIAN_EDITS: "review/edits.json",
    ArtifactType.FINAL_VERSION: "review/final.json",
    ArtifactType.EXPORT_PDF: "exports/final.pdf",
}


def build_artifact_key(
    clinic_id: str,
    consultation_id: str,
    artifact_type: ArtifactType,
) -> str:
    """Build the S3 object key for a consultation artifact.

    Pattern: clinics/{clinic_id}/consultations/{consultation_id}/{path}
    """
    path = _ARTIFACT_PATHS[artifact_type]
    return f"clinics/{clinic_id}/consultations/{consultation_id}/{path}"
