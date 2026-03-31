"""Unit tests for entitlement computation domain service."""

import unittest

from deskai.domain.auth.services import compute_entitlements
from deskai.domain.auth.value_objects import PlanType


class FreeTrialEntitlementsTest(unittest.TestCase):
    def test_free_trial_within_limits(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at="2026-03-20T00:00:00+00:00",
            consultations_used_this_month=3,
            now="2026-03-25T12:00:00+00:00",
        )
        self.assertTrue(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 7)
        self.assertEqual(e.consultations_used_this_month, 3)
        self.assertEqual(e.max_duration_minutes, 30)
        self.assertTrue(e.export_enabled)
        self.assertFalse(e.trial_expired)
        self.assertIsNotNone(e.trial_days_remaining)
        self.assertGreater(e.trial_days_remaining, 0)

    def test_free_trial_at_limit(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at="2026-03-20T00:00:00+00:00",
            consultations_used_this_month=10,
            now="2026-03-25T12:00:00+00:00",
        )
        self.assertFalse(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 0)

    def test_free_trial_expired(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at="2026-03-01T00:00:00+00:00",
            consultations_used_this_month=0,
            now="2026-03-20T00:00:00+00:00",
        )
        self.assertFalse(e.can_create_consultation)
        self.assertTrue(e.trial_expired)
        self.assertEqual(e.trial_days_remaining, 0)

    def test_free_trial_days_remaining(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at="2026-03-25T00:00:00+00:00",
            consultations_used_this_month=0,
            now="2026-03-30T00:00:00+00:00",
        )
        self.assertEqual(e.trial_days_remaining, 9)

    def test_free_trial_last_day(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at="2026-03-16T00:00:00+00:00",
            consultations_used_this_month=0,
            now="2026-03-29T23:59:59+00:00",
        )
        self.assertFalse(e.trial_expired)
        self.assertEqual(e.trial_days_remaining, 0)


class PlusEntitlementsTest(unittest.TestCase):
    def test_plus_within_limits(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.PLUS,
            created_at="2025-01-01T00:00:00+00:00",
            consultations_used_this_month=20,
            now="2026-03-25T12:00:00+00:00",
        )
        self.assertTrue(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 30)
        self.assertEqual(e.max_duration_minutes, 60)
        self.assertIsNone(e.trial_days_remaining)
        self.assertFalse(e.trial_expired)

    def test_plus_at_limit(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.PLUS,
            created_at="2025-01-01T00:00:00+00:00",
            consultations_used_this_month=50,
        )
        self.assertFalse(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 0)


class ProEntitlementsTest(unittest.TestCase):
    def test_pro_unlimited(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.PRO,
            created_at="2025-01-01T00:00:00+00:00",
            consultations_used_this_month=999,
        )
        self.assertTrue(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, -1)
        self.assertEqual(e.max_duration_minutes, 120)
        self.assertIsNone(e.trial_days_remaining)
        self.assertFalse(e.trial_expired)

    def test_export_always_enabled(self) -> None:
        for plan in PlanType:
            with self.subTest(plan=plan.value):
                e = compute_entitlements(
                    plan_type=plan,
                    created_at="2026-03-01T00:00:00+00:00",
                    consultations_used_this_month=0,
                    now="2026-03-05T00:00:00+00:00",
                )
                self.assertTrue(e.export_enabled)


if __name__ == "__main__":
    unittest.main()
