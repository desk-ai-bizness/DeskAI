"""Feature flag evaluator for plan-based entitlements."""

from deskai.bff.feature_flags.flags import (
    PLAN_FEATURE_FLAGS,
    PLAN_LIMITS,
    TRIAL_DURATION_DAYS,
)
from deskai.domain.auth.value_objects import PlanType


def evaluate_flags(
    plan_type: PlanType,
) -> dict[str, object]:
    """Resolve feature flag values for the given plan type."""
    limits = PLAN_LIMITS[plan_type]
    feature_flags = PLAN_FEATURE_FLAGS[plan_type]
    return {
        "consultation_monthly_limit": limits["monthly_limit"],
        "consultation_max_duration_minutes": limits[
            "max_duration_minutes"
        ],
        "audio_retention_days": limits["retention_days"],
        "export_pdf_enabled": feature_flags["export_pdf_enabled"],
        "insights_enabled": feature_flags["insights_enabled"],
        "audio_playback_enabled": feature_flags[
            "audio_playback_enabled"
        ],
        "trial_duration_days": TRIAL_DURATION_DAYS,
    }
