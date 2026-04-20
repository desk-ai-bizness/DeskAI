"""Unit tests for the WebSocket session init handler."""

import json
import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.value_objects import ConnectionInfo


def _make_connection():
    return ConnectionInfo(
        connection_id="conn-abc",
        session_id="",
        doctor_id="doc-001",
        clinic_id="clinic-001",
        connected_at="2026-04-02T10:00:00+00:00",
    )


def _make_session(**overrides):
    defaults = dict(
        session_id="sess-001",
        consultation_id="cons-001",
        doctor_id="doc-001",
        clinic_id="clinic-001",
        state=SessionState.ACTIVE,
        started_at="2026-04-02T10:00:00+00:00",
    )
    defaults.update(overrides)
    return Session(**defaults)


class HandleSessionInitTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.session_repo = MagicMock()
        self.apigw = MagicMock()

    def _make_event(self, consultation_id="cons-001", session_id="sess-001"):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$default",
            },
            "body": json.dumps(
                {
                    "action": "session.init",
                    "data": {
                        "consultation_id": consultation_id,
                        "session_id": session_id,
                    },
                }
            ),
        }

    @patch(
        "deskai.handlers.websocket.session_init_handler.utc_now_iso",
        return_value="2026-04-02T12:00:00+00:00",
    )
    def test_init_success(self, _mock_time):
        from deskai.handlers.websocket.session_init_handler import handle_session_init

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        session = _make_session()
        self.session_repo.find_by_id.return_value = session

        result = handle_session_init(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 200)
        self.session_repo.update.assert_called_once()
        updated = self.session_repo.update.call_args[0][0]
        self.assertEqual(updated.state, SessionState.RECORDING)
        self.assertEqual(updated.connection_id, "conn-abc")
        self.apigw.send_to_connection.assert_called_once()
        sent_data = self.apigw.send_to_connection.call_args[1]["data"]
        self.assertEqual(sent_data["event"], "session.status")
        self.assertEqual(sent_data["data"]["status"], "recording")

    def test_init_invalid_session(self):
        from deskai.handlers.websocket.session_init_handler import handle_session_init

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        self.session_repo.find_by_id.return_value = None

        result = handle_session_init(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 400)
        self.session_repo.update.assert_not_called()

    def test_init_wrong_doctor(self):
        from deskai.handlers.websocket.session_init_handler import handle_session_init

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        session = _make_session(doctor_id="doc-other")
        self.session_repo.find_by_id.return_value = session

        result = handle_session_init(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 403)
        self.session_repo.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
