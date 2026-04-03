"""Auth domain entities."""

import re
from dataclasses import dataclass

from deskai.domain.auth.value_objects import PlanType
from deskai.shared.errors import DomainValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class DoctorProfile:
    """Doctor identity and clinic context resolved from DynamoDB."""

    doctor_id: str
    identity_provider_id: str
    email: str
    name: str
    clinic_id: str
    clinic_name: str
    plan_type: PlanType
    created_at: str

    def __post_init__(self) -> None:
        if not self.doctor_id or not self.doctor_id.strip():
            raise DomainValidationError("doctor_id must be a non-empty string")
        if not self.identity_provider_id or not self.identity_provider_id.strip():
            raise DomainValidationError("identity_provider_id must be a non-empty string")
        if not self.email or not _EMAIL_RE.match(self.email):
            raise DomainValidationError("email must be a valid email address")
        if not self.name or not self.name.strip():
            raise DomainValidationError("name must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not self.clinic_name or not self.clinic_name.strip():
            raise DomainValidationError("clinic_name must be a non-empty string")
        if not isinstance(self.plan_type, PlanType):
            raise DomainValidationError(
                f"plan_type must be a PlanType, got {type(self.plan_type).__name__}"
            )
        if not self.created_at or not self.created_at.strip():
            raise DomainValidationError("created_at must be a non-empty string")
