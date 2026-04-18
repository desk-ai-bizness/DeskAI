"""Patient domain entities."""

from dataclasses import dataclass

from deskai.shared.errors import DomainValidationError


@dataclass(frozen=True)
class Patient:
    """Immutable patient identity within a clinic context."""

    patient_id: str
    name: str
    cpf: str
    clinic_id: str
    created_at: str
    date_of_birth: str | None = None

    def __post_init__(self) -> None:
        if not self.patient_id or not self.patient_id.strip():
            raise DomainValidationError("patient_id must be a non-empty string")
        if not self.name or not self.name.strip():
            raise DomainValidationError("name must be a non-empty string")
        if not self.cpf or not self.cpf.strip():
            raise DomainValidationError("cpf must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not self.created_at or not self.created_at.strip():
            raise DomainValidationError("created_at must be a non-empty string")
