"""Feature flag evaluator for plan-based entitlements."""

from deskai.bff.feature_flags.flags import (
    PLAN_LIMITS,
    TRIAL_DURATION_DAYS,
)
from deskai.domain.auth.value_objects import PlanType


def evaluate_flags(
    plan_type: PlanType,
) -> dict[str, object]:
    """Resolve feature flag values for the given plan type."""
    limits = PLAN_LIMITS[plan_type]
    return {
        "consultation_monthly_limit": limits["monthly_limit"],
        "consultation_max_duration_minutes": limits[
            "max_duration_minutes"
        ],
        "audio_retention_days": limits["retention_days"],
        "export_pdf_enabled": True,
        "insights_enabled": True,
        "audio_playback_enabled": False,
        "trial_duration_days": TRIAL_DURATION_DAYS,
    }
