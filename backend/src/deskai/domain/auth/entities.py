"""Auth domain entities."""

from dataclasses import dataclass

from deskai.domain.auth.value_objects import PlanType


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
