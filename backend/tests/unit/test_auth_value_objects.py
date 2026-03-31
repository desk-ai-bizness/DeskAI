"""Unit tests for auth domain value objects."""

import unittest

from deskai.domain.auth.value_objects import (
    AuthContext,
    Entitlements,
    PlanType,
    Tokens,
)


class PlanTypeTest(unittest.TestCase):
    def test_plan_type_values(self) -> None:
        self.assertEqual(PlanType.FREE_TRIAL.value, "free_trial")
        self.assertEqual(PlanType.PLUS.value, "plus")
        self.assertEqual(PlanType.PRO.value, "pro")

    def test_plan_type_from_string(self) -> None:
        self.assertEqual(PlanType("free_trial"), PlanType.FREE_TRIAL)
        self.assertEqual(PlanType("plus"), PlanType.PLUS)
        self.assertEqual(PlanType("pro"), PlanType.PRO)

    def test_all_plan_types_exist(self) -> None:
        values = {p.value for p in PlanType}
        self.assertEqual(values, {"free_trial", "plus", "pro"})


class AuthContextTest(unittest.TestCase):
    def test_auth_context_is_frozen(self) -> None:
        ctx = AuthContext(
            doctor_id="d1",
            email="a@b.com",
            clinic_id="c1",
            plan_type=PlanType.PLUS,
        )
        with self.assertRaises(AttributeError):
            ctx.doctor_id = "d2"

    def test_auth_context_fields(self) -> None:
        ctx = AuthContext(
            doctor_id="d1",
            email="a@b.com",
            clinic_id="c1",
            plan_type=PlanType.PRO,
        )
        self.assertEqual(ctx.doctor_id, "d1")
        self.assertEqual(ctx.plan_type, PlanType.PRO)


class TokensTest(unittest.TestCase):
    def test_tokens_is_frozen(self) -> None:
        t = Tokens(
            access_token="a",
            refresh_token="r",
            expires_in=3600,
        )
        with self.assertRaises(AttributeError):
            t.access_token = "x"

    def test_tokens_fields(self) -> None:
        t = Tokens(
            access_token="a",
            refresh_token="r",
            expires_in=7200,
        )
        self.assertEqual(t.expires_in, 7200)


class EntitlementsTest(unittest.TestCase):
    def test_entitlements_is_frozen(self) -> None:
        e = Entitlements(
            can_create_consultation=True,
            consultations_remaining=5,
            consultations_used_this_month=5,
            max_duration_minutes=30,
            export_enabled=True,
            trial_expired=False,
            trial_days_remaining=10,
        )
        with self.assertRaises(AttributeError):
            e.can_create_consultation = False


if __name__ == "__main__":
    unittest.main()
