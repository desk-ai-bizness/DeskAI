"""Consultation domain events."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsultationCreated:
    """Emitted when a new consultation is created."""

    consultation_id: str
    doctor_id: str
    clinic_id: str
    patient_id: str
    timestamp: str


@dataclass(frozen=True)
class ConsultationStatusChanged:
    """Emitted when a consultation transitions to a new status."""

    consultation_id: str
    from_status: str
    to_status: str
    actor_id: str
    timestamp: str
