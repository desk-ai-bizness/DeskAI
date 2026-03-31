"""Plan-scoped feature flag definitions.

Plan limits and trial duration are derived from the domain service to
avoid duplication.  The ``AUDIO_RETENTION_DAYS`` map is BFF-only (not a
domain concern) and therefore defined here.
"""

from deskai.domain.auth.services import (
    PLAN_MAX_DURATION_MINUTES,
    PLAN_MONTHLY_LIMITS,
    TRIAL_DURATION_DAYS,
)
from deskai.domain.auth.value_objects import PlanType

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
