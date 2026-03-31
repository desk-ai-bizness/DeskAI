"""Plan-scoped feature flag definitions."""

from deskai.domain.auth.value_objects import PlanType

PLAN_LIMITS: dict[PlanType, dict[str, int]] = {
    PlanType.FREE_TRIAL: {
        "monthly_limit": 10,
        "max_duration_minutes": 30,
        "retention_days": 7,
    },
    PlanType.PLUS: {
        "monthly_limit": 50,
        "max_duration_minutes": 60,
        "retention_days": 30,
    },
    PlanType.PRO: {
        "monthly_limit": -1,
        "max_duration_minutes": 120,
        "retention_days": 90,
    },
}

TRIAL_DURATION_DAYS = 14
