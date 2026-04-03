"""Unit tests for the GetUiConfig use case."""

import unittest
from deskai.application.config.get_ui_config import GetUiConfigUseCase
from deskai.bff.ui_config.bff_assembler_adapter import BffUiConfigAssembler
from deskai.domain.auth.value_objects import AuthContext, PlanType

class GetUiConfigUseCaseTest(unittest.TestCase):
    def setUp(self):
        self.uc = GetUiConfigUseCase(ui_config_assembler=BffUiConfigAssembler())
        self.ctx = AuthContext(doctor_id="d1", email="a@b.com", clinic_id="c1", plan_type=PlanType.PLUS)

    def test_returns_dict(self):
        self.assertIsInstance(self.uc.execute(self.ctx), dict)

    def test_has_version(self):
        self.assertEqual(self.uc.execute(self.ctx)["version"], "1.0")

    def test_has_all_keys(self):
        keys = {"version", "locale", "labels", "review_screen", "insight_categories", "status_labels", "feature_flags"}
        self.assertEqual(set(self.uc.execute(self.ctx).keys()), keys)

    def test_plus_export_enabled(self):
        self.assertTrue(self.uc.execute(self.ctx)["feature_flags"]["export_enabled"])

    def test_free_trial_export_disabled(self):
        ctx = AuthContext(doctor_id="d2", email="b@c.com", clinic_id="c2", plan_type=PlanType.FREE_TRIAL)
        self.assertFalse(self.uc.execute(ctx)["feature_flags"]["export_enabled"])

if __name__ == "__main__":
    unittest.main()
