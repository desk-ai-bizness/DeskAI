"""Unit tests for entitlement computation domain service."""

import unittest
from datetime import UTC, datetime

from deskai.domain.auth.services import compute_entitlements
from deskai.domain.auth.value_objects import PlanType


class FreeTrialEntitlementsTest(unittest.TestCase):
    def test_free_trial_within_limits(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at=datetime(2026, 3, 20, tzinfo=UTC),
            consultations_used_this_month=3,
            now=datetime(2026, 3, 25, 12, 0, 0, tzinfo=UTC),
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
            created_at=datetime(2026, 3, 20, tzinfo=UTC),
            consultations_used_this_month=10,
            now=datetime(2026, 3, 25, 12, 0, 0, tzinfo=UTC),
        )
        self.assertFalse(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 0)

    def test_free_trial_expired(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at=datetime(2026, 3, 1, tzinfo=UTC),
            consultations_used_this_month=0,
            now=datetime(2026, 3, 20, tzinfo=UTC),
        )
        self.assertFalse(e.can_create_consultation)
        self.assertTrue(e.trial_expired)
        self.assertEqual(e.trial_days_remaining, 0)

    def test_free_trial_days_remaining(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at=datetime(2026, 3, 25, tzinfo=UTC),
            consultations_used_this_month=0,
            now=datetime(2026, 3, 30, tzinfo=UTC),
        )
        self.assertEqual(e.trial_days_remaining, 9)

    def test_free_trial_last_day(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.FREE_TRIAL,
            created_at=datetime(2026, 3, 16, tzinfo=UTC),
            consultations_used_this_month=0,
            now=datetime(2026, 3, 29, 23, 59, 59, tzinfo=UTC),
        )
        self.assertFalse(e.trial_expired)
        self.assertEqual(e.trial_days_remaining, 0)


class PlusEntitlementsTest(unittest.TestCase):
    def test_plus_within_limits(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.PLUS,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            consultations_used_this_month=20,
            now=datetime(2026, 3, 25, 12, 0, 0, tzinfo=UTC),
        )
        self.assertTrue(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 30)
        self.assertEqual(e.max_duration_minutes, 60)
        self.assertIsNone(e.trial_days_remaining)
        self.assertFalse(e.trial_expired)

    def test_plus_at_limit(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.PLUS,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            consultations_used_this_month=50,
        )
        self.assertFalse(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 0)


class ProEntitlementsTest(unittest.TestCase):
    def test_pro_unlimited(self) -> None:
        e = compute_entitlements(
            plan_type=PlanType.PRO,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
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
                    created_at=datetime(2026, 3, 1, tzinfo=UTC),
                    consultations_used_this_month=0,
                    now=datetime(2026, 3, 5, tzinfo=UTC),
                )
                self.assertTrue(e.export_enabled)


if __name__ == "__main__":
    unittest.main()
