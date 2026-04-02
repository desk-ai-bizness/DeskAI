"""Patient domain entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Patient:
    """Immutable patient identity within a clinic context."""

    patient_id: str
    name: str
    date_of_birth: str
    clinic_id: str
    created_at: str
