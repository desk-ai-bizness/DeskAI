"""Consultation domain entities."""

from dataclasses import dataclass
from enum import StrEnum

from deskai.shared.errors import DomainValidationError


class ConsultationStatus(StrEnum):
    """Business states for a consultation lifecycle."""

    STARTED = "started"
    RECORDING = "recording"
    IN_PROCESSING = "in_processing"
    PROCESSING_FAILED = "processing_failed"
    DRAFT_GENERATED = "draft_generated"
    UNDER_PHYSICIAN_REVIEW = "under_physician_review"
    FINALIZED = "finalized"


@dataclass(frozen=True)
class Consultation:
    """Consultation aggregate root — immutable, transitions produce new instances."""

    consultation_id: str
    clinic_id: str
    doctor_id: str
    patient_id: str
    specialty: str
    status: ConsultationStatus = ConsultationStatus.STARTED
    scheduled_date: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    session_started_at: str | None = None
    session_ended_at: str | None = None
    processing_started_at: str | None = None
    processing_completed_at: str | None = None
    review_opened_at: str | None = None
    finalized_at: str | None = None
    finalized_by: str | None = None
    error_details: dict | None = None

    def __post_init__(self) -> None:
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not self.doctor_id or not self.doctor_id.strip():
            raise DomainValidationError("doctor_id must be a non-empty string")
        if not self.patient_id or not self.patient_id.strip():
            raise DomainValidationError("patient_id must be a non-empty string")
        if not self.specialty or not self.specialty.strip():
            raise DomainValidationError("specialty must be a non-empty string")
        if not isinstance(self.status, ConsultationStatus):
            raise DomainValidationError(f"status must be a ConsultationStatus, got {type(self.status).__name__}")
