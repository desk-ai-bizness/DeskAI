"""Export domain services."""


def build_export_s3_key(clinic_id: str, consultation_id: str) -> str:
    """Build the S3 object key for an export PDF."""
    return f"clinics/{clinic_id}/consultations/{consultation_id}/exports/final.pdf"


def build_final_version_s3_key(clinic_id: str, consultation_id: str) -> str:
    """Build the S3 key for the finalized JSON record."""
    return f"clinics/{clinic_id}/consultations/{consultation_id}/review/final.json"


def build_edits_s3_key(clinic_id: str, consultation_id: str) -> str:
    """Build the S3 key for physician edits."""
    return f"clinics/{clinic_id}/consultations/{consultation_id}/review/edits.json"
