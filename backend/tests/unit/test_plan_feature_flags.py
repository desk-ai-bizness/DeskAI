"""Unit tests for plan-dependent feature flags."""

import unittest
from deskai.bff.feature_flags.evaluator import evaluate_flags
from deskai.bff.feature_flags.flags import PLAN_FEATURE_FLAGS
from deskai.domain.auth.value_objects import PlanType

class PlanFeatureFlagsTest(unittest.TestCase):
    def test_free_trial_export_disabled(self):
        self.assertFalse(evaluate_flags(PlanType.FREE_TRIAL)["export_pdf_enabled"])

    def test_free_trial_insights_disabled(self):
        self.assertFalse(evaluate_flags(PlanType.FREE_TRIAL)["insights_enabled"])

    def test_plus_export_enabled(self):
        self.assertTrue(evaluate_flags(PlanType.PLUS)["export_pdf_enabled"])

    def test_pro_audio_playback_enabled(self):
        self.assertTrue(evaluate_flags(PlanType.PRO)["audio_playback_enabled"])

    def test_all_plans_have_flags(self):
        for p in PlanType:
            self.assertIn(p, PLAN_FEATURE_FLAGS)

if __name__ == "__main__":
    unittest.main()
