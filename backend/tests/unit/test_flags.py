"""Unit tests for plan-scoped feature flag definitions."""

import unittest

from deskai.bff.feature_flags.flags import (
    AUDIO_RETENTION_DAYS,
    PLAN_LIMITS,
)
from deskai.domain.auth.services import (
    PLAN_MAX_DURATION_MINUTES,
    PLAN_MONTHLY_LIMITS,
    TRIAL_DURATION_DAYS,
)
from deskai.domain.auth.value_objects import PlanType


class AudioRetentionDaysTest(unittest.TestCase):
    def test_free_trial_retention(self) -> None:
        self.assertEqual(
            AUDIO_RETENTION_DAYS[PlanType.FREE_TRIAL], 7
        )

    def test_plus_retention(self) -> None:
        self.assertEqual(AUDIO_RETENTION_DAYS[PlanType.PLUS], 30)

    def test_pro_retention(self) -> None:
        self.assertEqual(AUDIO_RETENTION_DAYS[PlanType.PRO], 90)

    def test_all_plans_covered(self) -> None:
        for plan in PlanType:
            self.assertIn(plan, AUDIO_RETENTION_DAYS)


class PlanLimitsTest(unittest.TestCase):
    def test_all_plans_present(self) -> None:
        for plan in PlanType:
            self.assertIn(plan, PLAN_LIMITS)

    def test_each_plan_has_required_keys(self) -> None:
        expected_keys = {
            "monthly_limit",
            "max_duration_minutes",
            "retention_days",
        }
        for plan in PlanType:
            self.assertEqual(
                set(PLAN_LIMITS[plan].keys()),
                expected_keys,
                f"Missing keys for {plan}",
            )

    def test_free_trial_monthly_limit(self) -> None:
        self.assertEqual(
            PLAN_LIMITS[PlanType.FREE_TRIAL]["monthly_limit"],
            PLAN_MONTHLY_LIMITS[PlanType.FREE_TRIAL],
        )

    def test_plus_monthly_limit(self) -> None:
        self.assertEqual(
            PLAN_LIMITS[PlanType.PLUS]["monthly_limit"],
            PLAN_MONTHLY_LIMITS[PlanType.PLUS],
        )

    def test_pro_unlimited(self) -> None:
        self.assertEqual(
            PLAN_LIMITS[PlanType.PRO]["monthly_limit"], -1
        )

    def test_max_duration_matches_domain(self) -> None:
        for plan in PlanType:
            self.assertEqual(
                PLAN_LIMITS[plan]["max_duration_minutes"],
                PLAN_MAX_DURATION_MINUTES[plan],
            )

    def test_retention_matches_audio_retention(self) -> None:
        for plan in PlanType:
            self.assertEqual(
                PLAN_LIMITS[plan]["retention_days"],
                AUDIO_RETENTION_DAYS[plan],
            )

    def test_trial_duration_days_value(self) -> None:
        self.assertEqual(TRIAL_DURATION_DAYS, 14)


if __name__ == "__main__":
    unittest.main()
