"""BFF view builder for the current-user profile response."""

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import Entitlements


def build_user_profile_view(
    profile: DoctorProfile,
    entitlements: Entitlements,
) -> dict:
    """Assemble the UserProfileView contract from domain objects."""
    return {
        "user": {
            "doctor_id": profile.doctor_id,
            "name": profile.name,
            "email": profile.email,
            "plan_type": profile.plan_type.value,
            "clinic_id": profile.clinic_id,
            "clinic_name": profile.clinic_name,
        },
        "entitlements": {
            "can_create_consultation": (
                entitlements.can_create_consultation
            ),
            "consultations_remaining": (
                entitlements.consultations_remaining
            ),
            "consultations_used_this_month": (
                entitlements.consultations_used_this_month
            ),
            "max_duration_minutes": (
                entitlements.max_duration_minutes
            ),
            "export_enabled": entitlements.export_enabled,
            "trial_expired": entitlements.trial_expired,
            "trial_days_remaining": (
                entitlements.trial_days_remaining
            ),
        },
    }
