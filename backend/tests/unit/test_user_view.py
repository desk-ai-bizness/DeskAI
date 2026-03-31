"""Unit tests for the BFF user profile view builder."""

import unittest

from deskai.bff.views.user_view import build_user_profile_view
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import (
    Entitlements,
    PlanType,
)


class UserViewTest(unittest.TestCase):
    def test_view_shape(self) -> None:
        profile = DoctorProfile(
            doctor_id="d1",
            cognito_sub="sub-1",
            email="doc@test.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic One",
            plan_type=PlanType.PLUS,
            created_at="2026-01-01T00:00:00+00:00",
        )
        entitlements = Entitlements(
            can_create_consultation=True,
            consultations_remaining=42,
            consultations_used_this_month=8,
            max_duration_minutes=60,
            export_enabled=True,
            trial_expired=False,
            trial_days_remaining=None,
        )
        view = build_user_profile_view(
            profile, entitlements
        )

        self.assertIn("user", view)
        self.assertIn("entitlements", view)
        self.assertEqual(view["user"]["doctor_id"], "d1")
        self.assertEqual(
            view["user"]["plan_type"], "plus"
        )
        self.assertEqual(
            view["user"]["clinic_name"], "Clinic One"
        )
        self.assertEqual(
            view["entitlements"]["consultations_remaining"],
            42,
        )
        self.assertIsNone(
            view["entitlements"]["trial_days_remaining"]
        )

    def test_plan_type_serialized_as_string(self) -> None:
        profile = DoctorProfile(
            doctor_id="d1",
            cognito_sub="sub-1",
            email="doc@test.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic",
            plan_type=PlanType.FREE_TRIAL,
            created_at="2026-01-01T00:00:00+00:00",
        )
        entitlements = Entitlements(
            can_create_consultation=True,
            consultations_remaining=10,
            consultations_used_this_month=0,
            max_duration_minutes=30,
            export_enabled=True,
            trial_expired=False,
            trial_days_remaining=14,
        )
        view = build_user_profile_view(
            profile, entitlements
        )
        self.assertEqual(
            view["user"]["plan_type"], "free_trial"
        )
        self.assertIsInstance(
            view["user"]["plan_type"], str
        )


if __name__ == "__main__":
    unittest.main()
