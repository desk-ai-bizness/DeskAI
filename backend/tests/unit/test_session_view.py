"""Unit tests for the session BFF views."""

import unittest

from deskai.domain.session.entities import Session, SessionState


class BuildSessionStartViewTest(unittest.TestCase):
    def test_build_session_start_view_has_correct_fields(self) -> None:
        from deskai.bff.views.session_view import build_session_start_view

        session = Session(
            session_id="sess-001",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ACTIVE,
            started_at="2026-04-02T10:00:00+00:00",
        )
        view = build_session_start_view(
            session,
            websocket_url="wss://ws.example.com/dev",
            max_duration_minutes=60,
        )

        self.assertEqual(view["session_id"], "sess-001")
        self.assertEqual(view["websocket_url"], "wss://ws.example.com/dev")
        self.assertEqual(view["connection_token"], "sess-001")
        self.assertEqual(view["max_duration_minutes"], 60)
        self.assertEqual(view["started_at"], "2026-04-02T10:00:00+00:00")

    def test_build_session_start_view_token_equals_session_id(self) -> None:
        from deskai.bff.views.session_view import build_session_start_view

        session = Session(
            session_id="unique-id-123",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            started_at="2026-04-02T10:00:00+00:00",
        )
        view = build_session_start_view(
            session,
            websocket_url="wss://ws.example.com/dev",
            max_duration_minutes=45,
        )

        self.assertEqual(view["connection_token"], view["session_id"])


class BuildSessionEndViewTest(unittest.TestCase):
    def test_build_session_end_view_has_correct_fields(self) -> None:
        from deskai.bff.views.session_view import build_session_end_view

        session = Session(
            session_id="sess-001",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ENDED,
            started_at="2026-04-02T10:00:00+00:00",
            ended_at="2026-04-02T10:30:00+00:00",
            duration_seconds=1800,
        )
        view = build_session_end_view(session)

        self.assertEqual(view["session_id"], "sess-001")
        self.assertEqual(view["ended_at"], "2026-04-02T10:30:00+00:00")
        self.assertEqual(view["duration_seconds"], 1800)
        self.assertEqual(view["status"], "in_processing")

    def test_build_session_end_view_status_always_in_processing(self) -> None:
        from deskai.bff.views.session_view import build_session_end_view

        session = Session(
            session_id="sess-002",
            consultation_id="cons-002",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ENDED,
            ended_at="2026-04-02T11:00:00+00:00",
            duration_seconds=600,
        )
        view = build_session_end_view(session)

        self.assertEqual(view["status"], "in_processing")


if __name__ == "__main__":
    unittest.main()
