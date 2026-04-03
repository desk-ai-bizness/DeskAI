"""Unit tests for HTTP handler middleware."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.exceptions import (
    AuthenticationError,
    DoctorProfileNotFoundError,
    PlanLimitExceededError,
    TrialExpiredError,
)
from deskai.domain.auth.value_objects import PlanType
from deskai.handlers.http.middleware import (
    error_response,
    extract_auth_context,
    handle_domain_errors,
    json_response,
    parse_json_body,
)


class ExtractAuthContextTest(unittest.TestCase):
    def _make_event(
        self,
        sub: str = "sub-1",
        email: str = "a@b.com",
    ) -> dict:
        return {
            "requestContext": {
                "authorizer": {
                    "jwt": {
                        "claims": {
                            "sub": sub,
                            "email": email,
                        }
                    }
                }
            }
        }

    def test_extracts_context_from_jwt_claims(
        self,
    ) -> None:
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
        mock_uc = MagicMock()
        mock_uc.execute.return_value = profile
        ctx = extract_auth_context(self._make_event(), mock_uc)
        self.assertEqual(ctx.doctor_id, "d1")
        self.assertEqual(ctx.clinic_id, "c1")
        self.assertEqual(ctx.plan_type, PlanType.PLUS)

    def test_raises_when_sub_missing(self) -> None:
        mock_uc = MagicMock()
        event = {"requestContext": {"authorizer": {"jwt": {"claims": {}}}}}
        with self.assertRaises(AuthenticationError):
            extract_auth_context(event, mock_uc)


class ErrorResponseTest(unittest.TestCase):
    def test_error_response_shape(self) -> None:
        resp = error_response(401, "unauthorized", "Bad creds")
        self.assertEqual(resp["statusCode"], 401)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "unauthorized")

    def test_json_response_shape(self) -> None:
        resp = json_response(200, {"key": "value"})
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["key"], "value")


class ParseJsonBodyTest(unittest.TestCase):
    def test_parses_valid_json(self) -> None:
        result = parse_json_body({"body": '{"email": "a@b.com"}'})
        self.assertEqual(result["email"], "a@b.com")

    def test_returns_empty_dict_for_missing_body(
        self,
    ) -> None:
        self.assertEqual(parse_json_body({}), {})

    def test_returns_empty_dict_for_invalid_json(
        self,
    ) -> None:
        self.assertEqual(parse_json_body({"body": "not json"}), {})

    # --- Adversarial inputs (API Gateway escaping) ---

    def test_strips_invalid_backslash_escape_from_exclamation(
        self,
    ) -> None:
        """API Gateway HTTP API v2 may inject \\! into the body."""
        result = parse_json_body({"body": '{"password": "Test123\\!"}'})
        self.assertEqual(result["password"], "Test123!")

    def test_strips_multiple_invalid_backslash_escapes(
        self,
    ) -> None:
        result = parse_json_body({"body": ('{"p": "a\\!b\\#c\\@d"}')})
        self.assertEqual(result["p"], "a!b#c@d")

    def test_preserves_valid_json_escapes(self) -> None:
        result = parse_json_body({"body": '{"msg": "line1\\nline2\\ttab"}'})
        self.assertEqual(result["msg"], "line1\nline2\ttab")

    def test_preserves_backslash_before_quote(
        self,
    ) -> None:
        result = parse_json_body({"body": '{"val": "say \\"hello\\""}'})
        self.assertEqual(result["val"], 'say "hello"')

    def test_preserves_unicode_escape(self) -> None:
        result = parse_json_body({"body": '{"val": "caf\\u00e9"}'})
        self.assertEqual(result["val"], "caf\u00e9")

    def test_parses_password_with_all_special_chars(
        self,
    ) -> None:
        """Realistic password with symbols that may be escaped."""
        body = '{"email":"a@b.com","password":"P@ss\\!w0rd\\#123"}'
        result = parse_json_body({"body": body})
        self.assertEqual(result["email"], "a@b.com")
        self.assertEqual(result["password"], "P@ss!w0rd#123")

    def test_handles_base64_encoded_body_with_special_chars(
        self,
    ) -> None:
        import base64

        raw = '{"password": "Test123!"}'
        encoded = base64.b64encode(raw.encode()).decode()
        result = parse_json_body({"body": encoded, "isBase64Encoded": True})
        self.assertEqual(result["password"], "Test123!")


class HandleDomainErrorsTest(unittest.TestCase):
    def test_maps_authentication_error_to_401(
        self,
    ) -> None:
        @handle_domain_errors
        def failing():
            raise AuthenticationError("bad")

        resp = failing()
        self.assertEqual(resp["statusCode"], 401)

    def test_maps_plan_limit_to_403(self) -> None:
        @handle_domain_errors
        def failing():
            raise PlanLimitExceededError("limit")

        resp = failing()
        self.assertEqual(resp["statusCode"], 403)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "plan_limit_exceeded")

    def test_maps_trial_expired_to_403(self) -> None:
        @handle_domain_errors
        def failing():
            raise TrialExpiredError("expired")

        resp = failing()
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "trial_expired")

    def test_maps_profile_not_found_to_403(
        self,
    ) -> None:
        @handle_domain_errors
        def failing():
            raise DoctorProfileNotFoundError("no profile")

        resp = failing()
        self.assertEqual(resp["statusCode"], 403)

    def test_unhandled_exception_returns_500(
        self,
    ) -> None:
        @handle_domain_errors
        def failing():
            raise RuntimeError("unexpected")

        resp = failing()
        self.assertEqual(resp["statusCode"], 500)


if __name__ == "__main__":
    unittest.main()
