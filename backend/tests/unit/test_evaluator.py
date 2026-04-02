"""Unit tests for the feature flag evaluator."""

import unittest

from deskai.bff.feature_flags.evaluator import evaluate_flags
from deskai.bff.feature_flags.flags import AUDIO_RETENTION_DAYS
from deskai.domain.auth.services import (
    PLAN_MAX_DURATION_MINUTES,
    PLAN_MONTHLY_LIMITS,
    TRIAL_DURATION_DAYS,
)
from deskai.domain.auth.value_objects import PlanType


class EvaluateFlagsTest(unittest.TestCase):
    def test_free_trial_limits(self) -> None:
        result = evaluate_flags(PlanType.FREE_TRIAL)

        self.assertEqual(
            result["consultation_monthly_limit"],
            PLAN_MONTHLY_LIMITS[PlanType.FREE_TRIAL],
        )
        self.assertEqual(
            result["consultation_max_duration_minutes"],
            PLAN_MAX_DURATION_MINUTES[PlanType.FREE_TRIAL],
        )
        self.assertEqual(
            result["audio_retention_days"],
            AUDIO_RETENTION_DAYS[PlanType.FREE_TRIAL],
        )

    def test_plus_limits(self) -> None:
        result = evaluate_flags(PlanType.PLUS)

        self.assertEqual(
            result["consultation_monthly_limit"],
            PLAN_MONTHLY_LIMITS[PlanType.PLUS],
        )
        self.assertEqual(
            result["consultation_max_duration_minutes"],
            PLAN_MAX_DURATION_MINUTES[PlanType.PLUS],
        )
        self.assertEqual(
            result["audio_retention_days"],
            AUDIO_RETENTION_DAYS[PlanType.PLUS],
        )

    def test_pro_limits(self) -> None:
        result = evaluate_flags(PlanType.PRO)

        self.assertEqual(
            result["consultation_monthly_limit"], -1
        )
        self.assertEqual(
            result["consultation_max_duration_minutes"],
            PLAN_MAX_DURATION_MINUTES[PlanType.PRO],
        )
        self.assertEqual(
            result["audio_retention_days"],
            AUDIO_RETENTION_DAYS[PlanType.PRO],
        )

    def test_static_flags_present(self) -> None:
        result = evaluate_flags(PlanType.PLUS)

        self.assertTrue(result["export_pdf_enabled"])
        self.assertTrue(result["insights_enabled"])
        self.assertFalse(result["audio_playback_enabled"])

    def test_trial_duration_days_included(self) -> None:
        result = evaluate_flags(PlanType.FREE_TRIAL)

        self.assertEqual(
            result["trial_duration_days"], TRIAL_DURATION_DAYS
        )

    def test_return_keys(self) -> None:
        result = evaluate_flags(PlanType.PLUS)

        expected_keys = {
            "consultation_monthly_limit",
            "consultation_max_duration_minutes",
            "audio_retention_days",
            "export_pdf_enabled",
            "insights_enabled",
            "audio_playback_enabled",
            "trial_duration_days",
        }
        self.assertEqual(set(result.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()
