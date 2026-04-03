"""Unit tests for the BFF feature flag evaluator."""

import unittest
from deskai.bff.feature_flags.evaluator import evaluate_flags
from deskai.domain.auth.value_objects import PlanType

class FeatureFlagEvaluatorTest(unittest.TestCase):
    def test_free_trial_limits(self):
        f = evaluate_flags(PlanType.FREE_TRIAL)
        self.assertEqual(f["consultation_monthly_limit"], 10)
        self.assertEqual(f["consultation_max_duration_minutes"], 30)
        self.assertEqual(f["audio_retention_days"], 7)

    def test_plus_limits(self):
        f = evaluate_flags(PlanType.PLUS)
        self.assertEqual(f["consultation_monthly_limit"], 50)

    def test_pro_limits(self):
        f = evaluate_flags(PlanType.PRO)
        self.assertEqual(f["consultation_monthly_limit"], -1)

    def test_export_paid_only(self):
        self.assertFalse(evaluate_flags(PlanType.FREE_TRIAL)["export_pdf_enabled"])
        self.assertTrue(evaluate_flags(PlanType.PLUS)["export_pdf_enabled"])
        self.assertTrue(evaluate_flags(PlanType.PRO)["export_pdf_enabled"])

    def test_audio_playback_pro_only(self):
        self.assertFalse(evaluate_flags(PlanType.FREE_TRIAL)["audio_playback_enabled"])
        self.assertFalse(evaluate_flags(PlanType.PLUS)["audio_playback_enabled"])
        self.assertTrue(evaluate_flags(PlanType.PRO)["audio_playback_enabled"])

if __name__ == "__main__":
    unittest.main()
