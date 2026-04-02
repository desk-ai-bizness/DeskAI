"""Consultation domain entities."""

from dataclasses import dataclass
from enum import StrEnum


class ConsultationStatus(StrEnum):
    """Business states for a consultation lifecycle."""

    STARTED = "started"
    RECORDING = "recording"
    IN_PROCESSING = "in_processing"
    PROCESSING_FAILED = "processing_failed"
    DRAFT_GENERATED = "draft_generated"
    UNDER_PHYSICIAN_REVIEW = "under_physician_review"
    FINALIZED = "finalized"


@dataclass
class Consultation:
    """Consultation aggregate root."""

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
