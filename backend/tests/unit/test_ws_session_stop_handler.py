"""Unit tests for the WebSocket session stop handler."""

import json
import unittest
from unittest.mock import MagicMock

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


class HandleSessionStopTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.end_session_use_case = MagicMock()
        self.apigw = MagicMock()

    def _make_event(self, consultation_id="cons-001"):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$default",
            },
            "body": json.dumps(
                {
                    "action": "session.stop",
                    "data": {"consultation_id": consultation_id},
                }
            ),
        }

    def test_stop_success(self):
        from deskai.handlers.websocket.session_stop_handler import handle_session_stop

        conn = _make_connection()
        self.connection_repo.find_by_connection_id.return_value = conn
        ended = Session(
            session_id="sess-001",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ENDED,
            started_at="2026-04-02T10:00:00+00:00",
            ended_at="2026-04-02T10:30:00+00:00",
        )
        self.end_session_use_case.execute.return_value = ended

        result = handle_session_stop(
            self._make_event(),
            self.connection_repo,
            self.end_session_use_case,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 200)
        self.end_session_use_case.execute.assert_called_once_with(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )
        self.apigw.send_to_connection.assert_called_once()
        sent = self.apigw.send_to_connection.call_args[1]["data"]
        self.assertEqual(sent["event"], "session.ended")
        self.assertEqual(sent["data"]["reason"], "manual")

    def test_stop_no_connection(self):
        from deskai.handlers.websocket.session_stop_handler import handle_session_stop

        self.connection_repo.find_by_connection_id.return_value = None

        result = handle_session_stop(
            self._make_event(),
            self.connection_repo,
            self.end_session_use_case,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 400)
        self.end_session_use_case.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
