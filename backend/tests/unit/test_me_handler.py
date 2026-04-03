"""Unit tests for the current-user profile handler."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.exceptions import (
    DoctorProfileNotFoundError,
)
from deskai.domain.auth.value_objects import (
    Entitlements,
    PlanType,
)
from deskai.handlers.http.me_handler import handle_get_me


def _me_event(sub: str = "sub-1") -> dict:
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {"claims": {"sub": sub}}
            }
        }
    }


class HandleGetMeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()

    def test_handle_get_me_success(self) -> None:
        profile = DoctorProfile(
            doctor_id="d1",
            identity_provider_id="sub-1",
            email="a@b.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic",
            plan_type=PlanType.PLUS,
            created_at="2026-01-01T00:00:00+00:00",
        )
        entitlements = Entitlements(
            can_create_consultation=True,
            consultations_remaining=10,
            consultations_used_this_month=5,
            max_duration_minutes=60,
            export_enabled=True,
            trial_expired=False,
            trial_days_remaining=None,
        )
        self.container.get_current_user.execute.return_value = (
            profile
        )
        self.container.check_entitlements.execute.return_value = (
            entitlements
        )

        resp = handle_get_me(_me_event("sub-1"), self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["user"]["doctor_id"], "d1")
        self.assertEqual(body["user"]["plan_type"], "plus")
        self.assertTrue(
            body["entitlements"]["can_create_consultation"]
        )

    def test_handle_get_me_user_not_found(self) -> None:
        self.container.get_current_user.execute.side_effect = (
            DoctorProfileNotFoundError("not found")
        )

        resp = handle_get_me(_me_event("sub-1"), self.container)

        self.assertEqual(resp["statusCode"], 403)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "forbidden")

    def test_handle_get_me_missing_sub(self) -> None:
        event = {
            "requestContext": {
                "authorizer": {"jwt": {"claims": {}}}
            }
        }
        resp = handle_get_me(event, self.container)

        self.assertEqual(resp["statusCode"], 401)


if __name__ == "__main__":
    unittest.main()
