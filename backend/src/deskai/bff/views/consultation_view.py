"""BFF view builders for consultation and patient responses."""

from deskai.application.patient.get_patient_detail import PatientDetailResult
from deskai.bff.action_availability import compute_actions, compute_warnings
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.patient.cpf import mask_cpf
from deskai.domain.patient.entities import Patient


def build_consultation_view(
    consultation: Consultation, patient_name: str = ""
) -> dict:
    """Assemble the standard consultation view contract."""
    return {
        "consultation_id": consultation.consultation_id,
        "patient": {
            "patient_id": consultation.patient_id,
            "name": patient_name,
        },
        "doctor_id": consultation.doctor_id,
        "clinic_id": consultation.clinic_id,
        "specialty": consultation.specialty,
        "status": consultation.status.value,
        "scheduled_date": consultation.scheduled_date,
        "created_at": consultation.created_at,
        "updated_at": consultation.updated_at,
    }


def build_consultation_list_view(
    consultations: list[Consultation],
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Assemble a list view with total count and pagination."""
    return {
        "consultations": [build_consultation_view(c) for c in consultations],
        "total_count": len(consultations),
        "page": page,
        "page_size": page_size,
    }


def build_consultation_detail_view(consultation: Consultation) -> dict:
    """Assemble a detailed view with session and processing metadata."""
    base = build_consultation_view(consultation)
    base.update({
        "session": {
            "session_id": None,
            "started_at": consultation.session_started_at,
            "ended_at": consultation.session_ended_at,
            "duration_seconds": None,
        },
        "processing": {
            "started_at": consultation.processing_started_at,
            "completed_at": consultation.processing_completed_at,
            "error_details": consultation.error_details,
        },
        "has_draft": consultation.status in (
            ConsultationStatus.DRAFT_GENERATED,
            ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
            ConsultationStatus.FINALIZED,
        ),
        "finalized_at": consultation.finalized_at,
        "finalized_by": consultation.finalized_by,
        "actions": compute_actions(consultation.status),
        "warnings": compute_warnings(
            consultation.status, consultation.error_details
        ),
    })
    return base


def build_patient_view(patient: Patient) -> dict:
    """Assemble the patient view contract."""
    return {
        "patient_id": patient.patient_id,
        "name": patient.name,
        "cpf": mask_cpf(patient.cpf),
        "date_of_birth": patient.date_of_birth,
        "clinic_id": patient.clinic_id,
        "created_at": patient.created_at,
    }


def build_patient_detail_view(result: PatientDetailResult) -> dict:
    """Assemble the patient detail/history view contract."""
    return {
        "patient": build_patient_view(result.patient),
        "history": [
            {
                "consultation_id": item.consultation.consultation_id,
                "status": item.consultation.status.value,
                "scheduled_date": item.consultation.scheduled_date,
                "finalized_at": item.consultation.finalized_at,
                "preview": item.preview,
            }
            for item in result.history
        ],
    }
