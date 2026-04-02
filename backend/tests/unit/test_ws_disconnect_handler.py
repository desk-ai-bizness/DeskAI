"""Unit tests for the WebSocket disconnect handler."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.value_objects import ConnectionInfo


def _make_connection(session_id="sess-001"):
    return ConnectionInfo(
        connection_id="conn-abc",
        session_id=session_id,
        doctor_id="doc-001",
        clinic_id="clinic-001",
        connected_at="2026-04-02T10:00:00+00:00",
    )


def _make_session(state=SessionState.RECORDING, **overrides):
    defaults = dict(
        session_id="sess-001",
        consultation_id="cons-001",
        doctor_id="doc-001",
        clinic_id="clinic-001",
        state=state,
        started_at="2026-04-02T10:00:00+00:00",
    )
    defaults.update(overrides)
    return Session(**defaults)


class HandleDisconnectTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.session_repo = MagicMock()

    def _make_event(self, connection_id="conn-abc"):
        return {
            "requestContext": {
                "connectionId": connection_id,
                "routeKey": "$disconnect",
            },
        }

    @patch(
        "deskai.handlers.websocket.disconnect_handler.utc_now_iso",
        return_value="2026-04-02T12:00:00+00:00",
    )
    def test_disconnect_with_active_session(self, _mock_time):
        from deskai.handlers.websocket.disconnect_handler import handle_disconnect

        conn = _make_connection(session_id="sess-001")
        self.connection_repo.find_by_connection_id.return_value = conn
        session = _make_session(state=SessionState.RECORDING)
        self.session_repo.find_by_id.return_value = session

        result = handle_disconnect(self._make_event(), self.connection_repo, self.session_repo)

        self.assertEqual(result["statusCode"], 200)
        self.session_repo.update.assert_called_once()
        updated = self.session_repo.update.call_args[0][0]
        self.assertEqual(updated.state, SessionState.DISCONNECTED)
        self.assertIsNotNone(updated.grace_period_expires_at)
        self.connection_repo.remove.assert_called_once_with("conn-abc")

    def test_disconnect_no_active_session(self):
        from deskai.handlers.websocket.disconnect_handler import handle_disconnect

        conn = _make_connection(session_id="")
        self.connection_repo.find_by_connection_id.return_value = conn

        result = handle_disconnect(self._make_event(), self.connection_repo, self.session_repo)

        self.assertEqual(result["statusCode"], 200)
        self.session_repo.update.assert_not_called()
        self.connection_repo.remove.assert_called_once_with("conn-abc")

    def test_disconnect_unknown_connection(self):
        from deskai.handlers.websocket.disconnect_handler import handle_disconnect

        self.connection_repo.find_by_connection_id.return_value = None

        result = handle_disconnect(self._make_event(), self.connection_repo, self.session_repo)

        self.assertEqual(result["statusCode"], 200)
        self.session_repo.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
