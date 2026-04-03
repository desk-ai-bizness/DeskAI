"""Auth domain value objects."""

import re
from dataclasses import dataclass
from enum import StrEnum

from deskai.shared.errors import DomainValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PlanType(StrEnum):
    """Supported subscription plan types."""

    FREE_TRIAL = "free_trial"
    PLUS = "plus"
    PRO = "pro"


@dataclass(frozen=True)
class AuthContext:
    """Authenticated request context resolved from Cognito claims and DynamoDB profile."""

    doctor_id: str
    email: str
    clinic_id: str
    plan_type: PlanType

    def __post_init__(self) -> None:
        if not self.doctor_id or not self.doctor_id.strip():
            raise DomainValidationError("doctor_id must be a non-empty string")
        if not self.email or not _EMAIL_RE.match(self.email):
            raise DomainValidationError("email must be a valid email address")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not isinstance(self.plan_type, PlanType):
            raise DomainValidationError(f"plan_type must be a PlanType, got {type(self.plan_type).__name__}")


@dataclass(frozen=True)
class Entitlements:
    """Plan-based access entitlements computed for a doctor."""

    can_create_consultation: bool
    consultations_remaining: int
    consultations_used_this_month: int
    max_duration_minutes: int
    export_enabled: bool
    trial_expired: bool
    trial_days_remaining: int | None

    def __post_init__(self) -> None:
        if self.consultations_remaining < -1:
            raise DomainValidationError("consultations_remaining must be non-negative or -1 (unlimited)")
        if self.consultations_used_this_month < 0:
            raise DomainValidationError("consultations_used_this_month must be non-negative")
        if self.max_duration_minutes < 0:
            raise DomainValidationError("max_duration_minutes must be non-negative")
        if self.trial_days_remaining is not None and self.trial_days_remaining < 0:
            raise DomainValidationError("trial_days_remaining must be non-negative when set")


@dataclass(frozen=True)
class Tokens:
    """Authentication tokens returned from Cognito."""

    access_token: str
    refresh_token: str
    expires_in: int

    def __post_init__(self) -> None:
        if not self.access_token or not self.access_token.strip():
            raise DomainValidationError("access_token must be a non-empty string")
        if not self.refresh_token or not self.refresh_token.strip():
            raise DomainValidationError("refresh_token must be a non-empty string")
        if self.expires_in <= 0:
            raise DomainValidationError("expires_in must be positive")
