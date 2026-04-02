"""Consultation business rule validators."""

from deskai.domain.consultation.entities import Consultation, ConsultationStatus


def validate_consultation_creation(
    patient_id: str,
    doctor_id: str,
    clinic_id: str,
    specialty: str,
) -> list[str]:
    """Validate inputs for creating a consultation.

    Returns a list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    if not patient_id:
        errors.append("patient_id is required")
    if not doctor_id:
        errors.append("doctor_id is required")
    if not clinic_id:
        errors.append("clinic_id is required")
    if not specialty:
        errors.append("specialty is required")

    return errors


def can_finalize(consultation: Consultation) -> bool:
    """Return True only if the consultation can be finalized."""
    return consultation.status == ConsultationStatus.UNDER_PHYSICIAN_REVIEW
