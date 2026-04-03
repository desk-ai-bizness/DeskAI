"""Unit tests for the BFF feature flag evaluator."""

import unittest

from deskai.bff.feature_flags.evaluator import (
    evaluate_flags,
)
from deskai.domain.auth.value_objects import PlanType


class FeatureFlagEvaluatorTest(unittest.TestCase):
    def test_free_trial_flags(self) -> None:
        flags = evaluate_flags(PlanType.FREE_TRIAL)
        self.assertEqual(
            flags["consultation_monthly_limit"], 10
        )
        self.assertEqual(
            flags["consultation_max_duration_minutes"], 30
        )
        self.assertEqual(
            flags["audio_retention_days"], 7
        )

    def test_plus_flags(self) -> None:
        flags = evaluate_flags(PlanType.PLUS)
        self.assertEqual(
            flags["consultation_monthly_limit"], 50
        )
        self.assertEqual(
            flags["consultation_max_duration_minutes"], 60
        )

    def test_pro_flags(self) -> None:
        flags = evaluate_flags(PlanType.PRO)
        self.assertEqual(
            flags["consultation_monthly_limit"], -1
        )
        self.assertEqual(
            flags["consultation_max_duration_minutes"],
            120,
        )

    def test_export_always_enabled(self) -> None:
        for plan in PlanType:
            with self.subTest(plan=plan.value):
                flags = evaluate_flags(plan)
                self.assertTrue(
                    flags["export_pdf_enabled"]
                )

    def test_audio_playback_disabled(self) -> None:
        flags = evaluate_flags(PlanType.PLUS)
        self.assertFalse(flags["audio_playback_enabled"])


if __name__ == "__main__":
    unittest.main()
