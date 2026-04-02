"""BFF view builders for consultation and patient responses."""

from deskai.domain.consultation.entities import Consultation
from deskai.domain.patient.entities import Patient


def build_consultation_view(consultation: Consultation) -> dict:
    """Assemble the standard consultation view contract."""
    return {
        "consultation_id": consultation.consultation_id,
        "patient_id": consultation.patient_id,
        "doctor_id": consultation.doctor_id,
        "clinic_id": consultation.clinic_id,
        "specialty": consultation.specialty,
        "status": consultation.status.value,
        "scheduled_date": consultation.scheduled_date,
        "created_at": consultation.created_at,
        "updated_at": consultation.updated_at,
    }


def build_consultation_list_view(consultations: list[Consultation]) -> dict:
    """Assemble a list view with total count."""
    return {
        "consultations": [build_consultation_view(c) for c in consultations],
        "total_count": len(consultations),
    }


def build_consultation_detail_view(consultation: Consultation) -> dict:
    """Assemble a detailed view with session and processing metadata."""
    base = build_consultation_view(consultation)
    base.update({
        "session": {
            "started_at": consultation.session_started_at,
            "ended_at": consultation.session_ended_at,
            "duration_seconds": None,
        },
        "processing": {
            "started_at": consultation.processing_started_at,
            "completed_at": consultation.processing_completed_at,
            "error_details": consultation.error_details,
        },
        "finalized_at": consultation.finalized_at,
        "finalized_by": consultation.finalized_by,
    })
    return base


def build_patient_view(patient: Patient) -> dict:
    """Assemble the patient view contract."""
    return {
        "patient_id": patient.patient_id,
        "name": patient.name,
        "date_of_birth": patient.date_of_birth,
        "clinic_id": patient.clinic_id,
        "created_at": patient.created_at,
    }
