"""Auth domain services — pure business rule computation."""

from datetime import UTC, datetime, timedelta

from deskai.domain.auth.value_objects import Entitlements, PlanType

PLAN_MONTHLY_LIMITS: dict[PlanType, int] = {
    PlanType.FREE_TRIAL: 10,
    PlanType.PLUS: 50,
    PlanType.PRO: -1,
}

PLAN_MAX_DURATION_MINUTES: dict[PlanType, int] = {
    PlanType.FREE_TRIAL: 30,
    PlanType.PLUS: 60,
    PlanType.PRO: 120,
}

TRIAL_DURATION_DAYS = 14


def compute_entitlements(
    plan_type: PlanType,
    created_at: datetime,
    consultations_used_this_month: int,
    now: datetime | None = None,
) -> Entitlements:
    """Compute plan entitlements from business rules.

    Args:
        plan_type: The doctor's current plan.
        created_at: Timezone-aware datetime of account creation.
        consultations_used_this_month: Number of consultations created this calendar month.
        now: Timezone-aware datetime for the current time. Defaults to UTC now.

    Returns:
        Computed entitlements with limits, trial status, and capability flags.
    """
    current_time = now if now else datetime.now(tz=UTC)
    monthly_limit = PLAN_MONTHLY_LIMITS[plan_type]

    trial_expired = False
    trial_days_remaining: int | None = None

    if plan_type == PlanType.FREE_TRIAL:
        trial_end = created_at + timedelta(days=TRIAL_DURATION_DAYS)
        trial_expired = current_time >= trial_end
        if not trial_expired:
            remaining_delta = trial_end - current_time
            trial_days_remaining = remaining_delta.days
        else:
            trial_days_remaining = 0

    if monthly_limit == -1:
        limit_reached = False
        consultations_remaining = -1
    else:
        limit_reached = consultations_used_this_month >= monthly_limit
        consultations_remaining = max(0, monthly_limit - consultations_used_this_month)

    can_create = not trial_expired and not limit_reached

    return Entitlements(
        can_create_consultation=can_create,
        consultations_remaining=consultations_remaining,
        consultations_used_this_month=consultations_used_this_month,
        max_duration_minutes=PLAN_MAX_DURATION_MINUTES[plan_type],
        export_enabled=True,
        trial_expired=trial_expired,
        trial_days_remaining=trial_days_remaining,
    )
