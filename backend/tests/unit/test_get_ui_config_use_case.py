"""Unit tests for the GetUiConfig use case."""

import unittest

from deskai.application.config.get_ui_config import (
    GetUiConfigUseCase,
)
from deskai.domain.auth.value_objects import AuthContext, PlanType


class GetUiConfigUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.use_case = GetUiConfigUseCase()
        self.auth_context = AuthContext(
            doctor_id="doc-001",
            email="dr.test@clinic.com",
            clinic_id="clinic-001",
            plan_type=PlanType.PLUS,
        )

    def test_execute_returns_dict(self) -> None:
        result = self.use_case.execute(self.auth_context)
        self.assertIsInstance(result, dict)

    def test_execute_returns_config_with_version(self) -> None:
        result = self.use_case.execute(self.auth_context)
        self.assertEqual(result["version"], "1.0")

    def test_execute_returns_config_with_locale(self) -> None:
        result = self.use_case.execute(self.auth_context)
        self.assertEqual(result["locale"], "pt-BR")

    def test_execute_uses_plan_type_from_auth_context(self) -> None:
        result = self.use_case.execute(self.auth_context)
        self.assertIn("feature_flags", result)

    def test_execute_returns_all_required_keys(self) -> None:
        result = self.use_case.execute(self.auth_context)
        expected_keys = {
            "version",
            "locale",
            "labels",
            "review_screen",
            "insight_categories",
            "status_labels",
            "feature_flags",
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_execute_with_free_trial_plan(self) -> None:
        ctx = AuthContext(
            doctor_id="doc-002",
            email="dr.trial@clinic.com",
            clinic_id="clinic-002",
            plan_type=PlanType.FREE_TRIAL,
        )
        result = self.use_case.execute(ctx)
        self.assertIn("feature_flags", result)

    def test_execute_with_pro_plan(self) -> None:
        ctx = AuthContext(
            doctor_id="doc-003",
            email="dr.pro@clinic.com",
            clinic_id="clinic-003",
            plan_type=PlanType.PRO,
        )
        result = self.use_case.execute(ctx)
        self.assertIn("feature_flags", result)


if __name__ == "__main__":
    unittest.main()
