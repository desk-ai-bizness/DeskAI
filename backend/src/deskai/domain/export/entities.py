"""Export domain entities."""

from dataclasses import dataclass

from deskai.domain.export.value_objects import ExportFormat
from deskai.shared.errors import DomainValidationError


@dataclass(frozen=True)
class ExportRequest:
    """Immutable request to generate a consultation export."""

    consultation_id: str
    clinic_id: str
    doctor_id: str
    format: ExportFormat = ExportFormat.PDF

    def __post_init__(self) -> None:
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not self.doctor_id or not self.doctor_id.strip():
            raise DomainValidationError("doctor_id must be a non-empty string")
        if not isinstance(self.format, ExportFormat):
            raise DomainValidationError(
                f"format must be an ExportFormat, got {type(self.format).__name__}"
            )


@dataclass(frozen=True)
class ExportArtifact:
    """Metadata about a generated and stored export."""

    consultation_id: str
    format: ExportFormat
    storage_key: str
    presigned_url: str
    expires_at: str

    def __post_init__(self) -> None:
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not self.storage_key or not self.storage_key.strip():
            raise DomainValidationError("storage_key must be a non-empty string")
