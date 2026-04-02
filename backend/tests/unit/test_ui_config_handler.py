"""Unit tests for the UI config HTTP handler."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.exceptions import (
    DoctorProfileNotFoundError,
)
from deskai.domain.auth.value_objects import PlanType
from deskai.handlers.http.ui_config_handler import (
    handle_get_ui_config,
)


def _config_event(sub: str = "sub-1") -> dict:
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {"claims": {"sub": sub, "email": "a@b.com"}}
            }
        }
    }


class HandleGetUiConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = DoctorProfile(
            doctor_id="d1",
            cognito_sub="sub-1",
            email="a@b.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic",
            plan_type=PlanType.PLUS,
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.container.get_current_user.execute.return_value = (
            self.profile
        )

    def test_returns_200_with_ui_config(self) -> None:
        resp = handle_get_ui_config(
            _config_event(), self.container
        )
        self.assertEqual(resp["statusCode"], 200)

    def test_response_body_has_required_keys(self) -> None:
        resp = handle_get_ui_config(
            _config_event(), self.container
        )
        body = json.loads(resp["body"])
        expected_keys = {
            "version",
            "locale",
            "labels",
            "review_screen",
            "insight_categories",
            "status_labels",
            "feature_flags",
        }
        self.assertEqual(set(body.keys()), expected_keys)

    def test_response_version_and_locale(self) -> None:
        resp = handle_get_ui_config(
            _config_event(), self.container
        )
        body = json.loads(resp["body"])
        self.assertEqual(body["version"], "1.0")
        self.assertEqual(body["locale"], "pt-BR")

    def test_missing_sub_returns_401(self) -> None:
        event = {
            "requestContext": {
                "authorizer": {"jwt": {"claims": {}}}
            }
        }
        resp = handle_get_ui_config(event, self.container)
        self.assertEqual(resp["statusCode"], 401)

    def test_doctor_not_found_returns_403(self) -> None:
        self.container.get_current_user.execute.side_effect = (
            DoctorProfileNotFoundError("not found")
        )
        resp = handle_get_ui_config(
            _config_event(), self.container
        )
        self.assertEqual(resp["statusCode"], 403)

    def test_feature_flags_are_booleans(self) -> None:
        resp = handle_get_ui_config(
            _config_event(), self.container
        )
        body = json.loads(resp["body"])
        flags = body["feature_flags"]
        self.assertIsInstance(flags["export_enabled"], bool)
        self.assertIsInstance(flags["insights_enabled"], bool)
        self.assertIsInstance(
            flags["audio_playback_enabled"], bool
        )


if __name__ == "__main__":
    unittest.main()
