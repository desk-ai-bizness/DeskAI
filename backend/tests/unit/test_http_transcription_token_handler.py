"""Unit tests for the transcription-token HTTP handler."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.auth.value_objects import PlanType
from deskai.domain.consultation.exceptions import ConsultationNotFoundError
from deskai.domain.session.exceptions import InvalidSessionStateError


def _make_event(consultation_id="cons-001"):
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": "identity-001",
                        "email": "doc@clinic.com",
                    }
                }
            },
            "http": {
                "method": "POST",
                "path": f"/v1/consultations/{consultation_id}/transcription-token",
            },
            "requestId": "req-001",
        },
        "pathParameters": {"id": consultation_id},
    }


class TranscriptionTokenHandlerTest(unittest.TestCase):
    def setUp(self):
        self.container = MagicMock()
        self.container.get_current_user.execute.return_value = MagicMock(
            doctor_id="doc-001",
            email="doc@clinic.com",
            clinic_id="clinic-001",
            plan_type=PlanType.PRO,
        )

    def test_token_issued_successfully(self):
        from deskai.handlers.http.transcription_token_handler import (
            handle_get_transcription_token,
        )

        self.container.issue_transcription_token.execute.return_value = {
            "token": "el-token-xyz",
            "expires_at": "2026-04-19T11:00:00+00:00",
        }

        result = handle_get_transcription_token(_make_event(), self.container)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["token"], "el-token-xyz")
        self.container.issue_transcription_token.execute.assert_called_once_with(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

    def test_missing_consultation_id(self):
        from deskai.handlers.http.transcription_token_handler import (
            handle_get_transcription_token,
        )

        event = _make_event()
        event["pathParameters"] = {}

        result = handle_get_transcription_token(event, self.container)

        self.assertEqual(result["statusCode"], 400)

    def test_consultation_not_found(self):
        from deskai.handlers.http.transcription_token_handler import (
            handle_get_transcription_token,
        )

        self.container.issue_transcription_token.execute.side_effect = (
            ConsultationNotFoundError("not found")
        )

        result = handle_get_transcription_token(_make_event(), self.container)

        self.assertEqual(result["statusCode"], 404)

    def test_invalid_session_state(self):
        from deskai.handlers.http.transcription_token_handler import (
            handle_get_transcription_token,
        )

        self.container.issue_transcription_token.execute.side_effect = (
            InvalidSessionStateError("not recording")
        )

        result = handle_get_transcription_token(_make_event(), self.container)

        self.assertEqual(result["statusCode"], 409)


if __name__ == "__main__":
    unittest.main()
