"""BFF view builder for the current-user profile response."""

from deskai.bff.feature_flags.evaluator import evaluate_flags
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
        "feature_flags": _build_feature_flags(profile.plan_type),
    }


def _build_feature_flags(plan_type) -> dict[str, object]:
    """Extract the UI-relevant feature flag subset."""
    flags = evaluate_flags(plan_type)
    return {
        "export_enabled": flags["export_pdf_enabled"],
        "insights_enabled": flags["insights_enabled"],
        "audio_playback_enabled": flags["audio_playback_enabled"],
    }
