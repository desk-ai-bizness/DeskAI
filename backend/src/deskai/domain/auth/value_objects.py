"""Auth domain value objects."""

from dataclasses import dataclass
from enum import StrEnum


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


@dataclass(frozen=True)
class Tokens:
    """Authentication tokens returned from Cognito."""

    access_token: str
    refresh_token: str
    expires_in: int
