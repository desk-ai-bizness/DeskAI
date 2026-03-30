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
    """Minimal consultation aggregate root placeholder."""

    consultation_id: str
    clinic_id: str
    doctor_id: str
    patient_id: str
    specialty: str
    status: ConsultationStatus = ConsultationStatus.STARTED
