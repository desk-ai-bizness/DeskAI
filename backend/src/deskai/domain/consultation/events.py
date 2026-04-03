"""Consultation domain events."""

from dataclasses import dataclass

from deskai.shared.errors import DomainValidationError


@dataclass(frozen=True)
class ConsultationCreated:
    """Emitted when a new consultation is created."""

    consultation_id: str
    doctor_id: str
    clinic_id: str
    patient_id: str
    timestamp: str

    def __post_init__(self) -> None:
        for field in ("consultation_id", "doctor_id", "clinic_id", "patient_id", "timestamp"):
            val = getattr(self, field)
            if not val or not val.strip():
                raise DomainValidationError(f"{field} must be a non-empty string")


@dataclass(frozen=True)
class ConsultationStatusChanged:
    """Emitted when a consultation transitions to a new status."""

    consultation_id: str
    from_status: str
    to_status: str
    actor_id: str
    timestamp: str

    def __post_init__(self) -> None:
        for field in ("consultation_id", "from_status", "to_status", "actor_id", "timestamp"):
            val = getattr(self, field)
            if not val or not val.strip():
                raise DomainValidationError(f"{field} must be a non-empty string")
