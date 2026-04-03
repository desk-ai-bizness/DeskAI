"""Plan-scoped feature flag definitions.

Plan limits and trial duration are derived from the domain service to
avoid duplication.  The ``AUDIO_RETENTION_DAYS`` map is BFF-only (not a
domain concern) and therefore defined here.
"""

from deskai.domain.auth.services import (
    PLAN_MAX_DURATION_MINUTES,
    PLAN_MONTHLY_LIMITS,
    TRIAL_DURATION_DAYS,  # re-exported for evaluator.py
)
from deskai.domain.auth.value_objects import PlanType

__all__ = [
    "PLAN_LIMITS",
    "TRIAL_DURATION_DAYS",
    "AUDIO_RETENTION_DAYS",
    "PLAN_FEATURE_FLAGS",
]

AUDIO_RETENTION_DAYS: dict[PlanType, int] = {
    PlanType.FREE_TRIAL: 7,
    PlanType.PLUS: 30,
    PlanType.PRO: 90,
}

PLAN_LIMITS: dict[PlanType, dict[str, int]] = {
    plan: {
        "monthly_limit": PLAN_MONTHLY_LIMITS[plan],
        "max_duration_minutes": PLAN_MAX_DURATION_MINUTES[plan],
        "retention_days": AUDIO_RETENTION_DAYS[plan],
    }
    for plan in PlanType
}

PLAN_FEATURE_FLAGS: dict[PlanType, dict[str, bool]] = {
    PlanType.FREE_TRIAL: {
        "export_pdf_enabled": False,
        "insights_enabled": False,
        "audio_playback_enabled": False,
    },
    PlanType.PLUS: {
        "export_pdf_enabled": True,
        "insights_enabled": True,
        "audio_playback_enabled": False,
    },
    PlanType.PRO: {
        "export_pdf_enabled": True,
        "insights_enabled": True,
        "audio_playback_enabled": True,
    },
}
