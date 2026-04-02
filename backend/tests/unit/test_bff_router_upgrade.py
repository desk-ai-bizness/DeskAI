"""Unit tests for the BFF router upgrade with parameterized routes."""

import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

if "infra" not in sys.modules:
    _infra_pkg = types.ModuleType("infra")
    _infra_pkg.__path__ = [str(Path(_REPO_ROOT) / "infra")]
    sys.modules["infra"] = _infra_pkg

from infra.lambda_handlers.bff import handler


def _api_event(
    path: str = "/",
    method: str = "GET",
    body: str = "",
    cognito_sub: str = "cognito-sub-001",
    email: str = "dr.test@clinic.com",
) -> dict:
    event: dict = {
        "rawPath": path,
        "requestContext": {
            "http": {"method": method},
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": cognito_sub,
                        "email": email,
                    },
                },
            },
        },
        "headers": {"content-type": "application/json"},
    }
    if body:
        event["body"] = body
    return event


class BffRouterUpgradeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.patcher = patch(
            "infra.lambda_handlers.bff._get_container",
            return_value=self.container,
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()

    @patch(
        "deskai.handlers.http.consultation_handler.handle_get_consultation"
    )
    def test_parameterized_route_matches_consultation_id(
        self, mock_handler: MagicMock
    ) -> None:
        mock_handler.return_value = {
            "statusCode": 200,
            "body": "{}",
        }
        event = _api_event("/v1/consultations/cons-123", "GET")
        handler(event, MagicMock())

        mock_handler.assert_called_once()
        call_event = mock_handler.call_args[0][0]
        self.assertEqual(
            call_event.get("pathParameters", {}).get("id"),
            "cons-123",
        )

    @patch(
        "deskai.handlers.http.auth_handler.handle_login"
    )
    def test_exact_routes_still_work(
        self, mock_login: MagicMock
    ) -> None:
        mock_login.return_value = {
            "statusCode": 200,
            "body": "{}",
        }
        event = _api_event("/v1/auth/session", "POST")
        handler(event, MagicMock())

        mock_login.assert_called_once_with(event, self.container)

    def test_unknown_route_returns_404(self) -> None:
        resp = handler(
            _api_event("/v1/nonexistent", "GET"),
            MagicMock(),
        )
        self.assertEqual(resp["statusCode"], 404)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "not_found")

    @patch(
        "deskai.handlers.http.consultation_handler.handle_get_consultation"
    )
    def test_path_parameters_injected_into_event(
        self, mock_handler: MagicMock
    ) -> None:
        mock_handler.return_value = {
            "statusCode": 200,
            "body": "{}",
        }
        event = _api_event("/v1/consultations/abc-456", "GET")
        handler(event, MagicMock())

        call_event = mock_handler.call_args[0][0]
        self.assertIn("pathParameters", call_event)
        self.assertEqual(
            call_event["pathParameters"]["id"], "abc-456"
        )

    @patch(
        "deskai.handlers.http.consultation_handler.handle_create_consultation"
    )
    def test_post_consultations_route(
        self, mock_handler: MagicMock
    ) -> None:
        mock_handler.return_value = {
            "statusCode": 201,
            "body": "{}",
        }
        event = _api_event(
            "/v1/consultations",
            "POST",
            body=json.dumps({"patient_id": "p1"}),
        )
        handler(event, MagicMock())
        mock_handler.assert_called_once()

    @patch(
        "deskai.handlers.http.consultation_handler.handle_list_consultations"
    )
    def test_get_consultations_route(
        self, mock_handler: MagicMock
    ) -> None:
        mock_handler.return_value = {
            "statusCode": 200,
            "body": "{}",
        }
        event = _api_event("/v1/consultations", "GET")
        handler(event, MagicMock())
        mock_handler.assert_called_once()

    @patch(
        "deskai.handlers.http.patient_handler.handle_create_patient"
    )
    def test_post_patients_route(
        self, mock_handler: MagicMock
    ) -> None:
        mock_handler.return_value = {
            "statusCode": 201,
            "body": "{}",
        }
        event = _api_event(
            "/v1/patients",
            "POST",
            body=json.dumps({"name": "Joao"}),
        )
        handler(event, MagicMock())
        mock_handler.assert_called_once()

    @patch(
        "deskai.handlers.http.patient_handler.handle_list_patients"
    )
    def test_get_patients_route(
        self, mock_handler: MagicMock
    ) -> None:
        mock_handler.return_value = {
            "statusCode": 200,
            "body": "{}",
        }
        event = _api_event("/v1/patients", "GET")
        handler(event, MagicMock())
        mock_handler.assert_called_once()


if __name__ == "__main__":
    unittest.main()
