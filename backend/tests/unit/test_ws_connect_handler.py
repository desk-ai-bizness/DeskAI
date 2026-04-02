"""Unit tests for the WebSocket connect handler."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.session.value_objects import ConnectionInfo


class HandleConnectTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.auth_provider = MagicMock()

    def _make_connect_event(self, token="valid-token"):
        event = {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$connect",
            },
        }
        if token is not None:
            event["queryStringParameters"] = {"token": token}
        else:
            event["queryStringParameters"] = None
        return event

    @patch(
        "deskai.handlers.websocket.connect_handler.utc_now_iso",
        return_value="2026-04-02T12:00:00+00:00",
    )
    def test_connect_success(self, _mock_time):
        from deskai.handlers.websocket.connect_handler import handle_connect

        self.auth_provider.validate_ws_token.return_value = {
            "doctor_id": "doc-001",
            "clinic_id": "clinic-001",
        }

        event = self._make_connect_event(token="valid-token")
        result = handle_connect(event, self.connection_repo, self.auth_provider)

        self.assertEqual(result["statusCode"], 200)
        self.connection_repo.save.assert_called_once()
        saved = self.connection_repo.save.call_args[0][0]
        self.assertIsInstance(saved, ConnectionInfo)
        self.assertEqual(saved.connection_id, "conn-abc")
        self.assertEqual(saved.doctor_id, "doc-001")
        self.assertEqual(saved.clinic_id, "clinic-001")

    def test_connect_missing_token(self):
        from deskai.handlers.websocket.connect_handler import handle_connect

        event = self._make_connect_event(token=None)
        result = handle_connect(event, self.connection_repo, self.auth_provider)

        self.assertEqual(result["statusCode"], 401)
        self.connection_repo.save.assert_not_called()

    def test_connect_invalid_token(self):
        from deskai.handlers.websocket.connect_handler import handle_connect

        self.auth_provider.validate_ws_token.side_effect = ValueError("Invalid token")

        event = self._make_connect_event(token="bad-token")
        result = handle_connect(event, self.connection_repo, self.auth_provider)

        self.assertEqual(result["statusCode"], 401)
        self.connection_repo.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
