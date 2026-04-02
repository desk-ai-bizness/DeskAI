"""Unit tests for the session HTTP handlers."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import (
    InvalidSessionStateError,
    SessionNotActiveError,
)
from tests.conftest import (
    make_apigw_event,
    make_sample_doctor_profile,
)


def _make_container_with_session_mocks() -> MagicMock:
    """Build a mock container with start_session and end_session use cases."""
    container = MagicMock()
    profile = make_sample_doctor_profile()
    container.get_current_user.execute.return_value = profile
    container.settings.websocket_url = "wss://ws.example.com/dev"
    container.settings.max_session_duration_minutes = 60
    return container


def _make_sample_session(**overrides) -> Session:
    """Build a Session entity with sensible defaults."""
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


# ---- Start Session Tests ----


class HandleStartSessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = _make_container_with_session_mocks()

    def test_handle_start_session_success(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_start_session,
        )

        session = _make_sample_session()
        self.container.start_session.execute.return_value = session

        event = make_apigw_event(
            path="/v1/consultations/cons-001/session/start",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_start_session(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["session_id"], "sess-001")
        self.assertEqual(body["websocket_url"], "wss://ws.example.com/dev")
        self.assertEqual(body["connection_token"], "sess-001")
        self.assertEqual(body["max_duration_minutes"], 60)
        self.assertEqual(body["started_at"], "2026-04-02T10:00:00+00:00")

    def test_handle_start_session_missing_consultation_id(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_start_session,
        )

        event = make_apigw_event(
            path="/v1/consultations//session/start",
            method="POST",
        )
        resp = handle_start_session(event, self.container)

        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "validation_error")

    def test_handle_start_session_consultation_not_found(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_start_session,
        )

        self.container.start_session.execute.side_effect = (
            ConsultationNotFoundError("Not found")
        )

        event = make_apigw_event(
            path="/v1/consultations/cons-missing/session/start",
            method="POST",
            path_parameters={"id": "cons-missing"},
        )
        resp = handle_start_session(event, self.container)

        self.assertEqual(resp["statusCode"], 404)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "not_found")

    def test_handle_start_session_ownership_error(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_start_session,
        )

        self.container.start_session.execute.side_effect = (
            ConsultationOwnershipError("Not your consultation")
        )

        event = make_apigw_event(
            path="/v1/consultations/cons-001/session/start",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_start_session(event, self.container)

        self.assertEqual(resp["statusCode"], 403)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "forbidden")

    def test_handle_start_session_invalid_state(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_start_session,
        )

        self.container.start_session.execute.side_effect = (
            InvalidSessionStateError("Session already active")
        )

        event = make_apigw_event(
            path="/v1/consultations/cons-001/session/start",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_start_session(event, self.container)

        self.assertEqual(resp["statusCode"], 409)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "conflict")


# ---- End Session Tests ----


class HandleEndSessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = _make_container_with_session_mocks()

    def test_handle_end_session_success(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_end_session,
        )

        session = _make_sample_session(
            state=SessionState.ENDED,
            ended_at="2026-04-02T10:30:00+00:00",
            duration_seconds=1800,
        )
        self.container.end_session.execute.return_value = session

        event = make_apigw_event(
            path="/v1/consultations/cons-001/session/end",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_end_session(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["session_id"], "sess-001")
        self.assertEqual(body["ended_at"], "2026-04-02T10:30:00+00:00")
        self.assertEqual(body["duration_seconds"], 1800)
        self.assertEqual(body["status"], "in_processing")

    def test_handle_end_session_not_found(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_end_session,
        )

        self.container.end_session.execute.side_effect = (
            ConsultationNotFoundError("Not found")
        )

        event = make_apigw_event(
            path="/v1/consultations/cons-missing/session/end",
            method="POST",
            path_parameters={"id": "cons-missing"},
        )
        resp = handle_end_session(event, self.container)

        self.assertEqual(resp["statusCode"], 404)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "not_found")

    def test_handle_end_session_ownership_error(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_end_session,
        )

        self.container.end_session.execute.side_effect = (
            ConsultationOwnershipError("Not your consultation")
        )

        event = make_apigw_event(
            path="/v1/consultations/cons-001/session/end",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_end_session(event, self.container)

        self.assertEqual(resp["statusCode"], 403)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "forbidden")

    def test_handle_end_session_no_active_session(self) -> None:
        from deskai.handlers.http.session_handler import (
            handle_end_session,
        )

        self.container.end_session.execute.side_effect = (
            SessionNotActiveError("No active session")
        )

        event = make_apigw_event(
            path="/v1/consultations/cons-001/session/end",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_end_session(event, self.container)

        self.assertEqual(resp["statusCode"], 404)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "not_found")


if __name__ == "__main__":
    unittest.main()
