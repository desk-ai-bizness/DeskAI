"""Unit tests for new WebSocket handlers: transcript.commit, session.pause, session.resume."""

import json
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


class TranscriptCommitHandlerTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.session_repo = MagicMock()
        self.segment_repo = MagicMock()
        self.apigw = MagicMock()

    def _make_event(self):
        return {
            "requestContext": {"connectionId": "conn-abc"},
            "body": json.dumps({
                "action": "transcript.commit",
                "data": {
                    "consultation_id": "cons-001",
                    "segments": [
                        {
                            "speaker": "doctor",
                            "text": "Como voce esta?",
                            "start_time": 0.0,
                            "end_time": 1.5,
                            "confidence": 0.95,
                            "is_final": True,
                        }
                    ],
                    "timestamp": "2026-04-02T10:05:00+00:00",
                },
            }),
        }

    def test_commit_accepted(self):
        from deskai.handlers.websocket.transcript_commit_handler import (
            handle_transcript_commit,
        )

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        self.session_repo.find_by_id.return_value = _make_session()
        self.segment_repo.find_by_consultation.return_value = []

        with patch(
            "deskai.handlers.websocket.transcript_commit_handler.utc_now_iso",
            return_value="2026-04-02T10:05:00+00:00",
        ):
            result = handle_transcript_commit(
                self._make_event(),
                self.connection_repo,
                self.session_repo,
                self.segment_repo,
                self.apigw,
            )

        self.assertEqual(result["statusCode"], 200)
        self.segment_repo.save_batch.assert_called_once()

    def test_commit_emits_provisional_workspace_events(self):
        from deskai.handlers.websocket.transcript_commit_handler import (
            handle_transcript_commit,
        )

        event = {
            "requestContext": {"connectionId": "conn-abc"},
            "body": json.dumps({
                "action": "transcript.commit",
                "data": {
                    "consultation_id": "cons-001",
                    "segments": [
                        {
                            "speaker": "patient",
                            "text": "Estou com dor de cabeca.",
                            "start_time": 0.0,
                            "end_time": 1.5,
                            "confidence": 0.95,
                            "is_final": True,
                        }
                    ],
                    "timestamp": "2026-04-02T10:05:00+00:00",
                },
            }),
        }
        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        self.session_repo.find_by_id.return_value = _make_session()
        self.segment_repo.find_by_consultation.return_value = []

        with patch(
            "deskai.handlers.websocket.transcript_commit_handler.utc_now_iso",
            return_value="2026-04-02T10:05:00+00:00",
        ):
            result = handle_transcript_commit(
                event,
                self.connection_repo,
                self.session_repo,
                self.segment_repo,
                self.apigw,
            )

        self.assertEqual(result["statusCode"], 200)
        emitted_events = [
            call.kwargs["data"]["event"] for call in self.apigw.send_to_connection.call_args_list
        ]
        self.assertIn("autofill.candidate", emitted_events)
        self.assertIn("insight.provisional", emitted_events)

    def test_commit_unknown_connection(self):
        from deskai.handlers.websocket.transcript_commit_handler import (
            handle_transcript_commit,
        )

        self.connection_repo.find_by_connection_id.return_value = None

        result = handle_transcript_commit(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.segment_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 400)

    def test_commit_not_recording_rejects(self):
        from deskai.handlers.websocket.transcript_commit_handler import (
            handle_transcript_commit,
        )

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        self.session_repo.find_by_id.return_value = _make_session(state=SessionState.ENDED)

        result = handle_transcript_commit(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.segment_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 400)
        self.segment_repo.save_batch.assert_not_called()


class SessionPauseHandlerTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.pause_use_case = MagicMock()
        self.apigw = MagicMock()

    def _make_event(self):
        return {
            "requestContext": {"connectionId": "conn-abc"},
            "body": json.dumps({
                "action": "session.pause",
                "data": {
                    "consultation_id": "cons-001",
                    "timestamp": "2026-04-02T10:05:00+00:00",
                },
            }),
        }

    def test_pause_success(self):
        from deskai.handlers.websocket.session_pause_handler import (
            handle_session_pause,
        )

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        self.pause_use_case.execute.return_value = _make_session(state=SessionState.PAUSED)

        result = handle_session_pause(
            self._make_event(),
            self.connection_repo,
            self.pause_use_case,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 200)
        self.pause_use_case.execute.assert_called_once()
        self.apigw.send_to_connection.assert_called_once()
        sent = self.apigw.send_to_connection.call_args[1]["data"]
        self.assertEqual(sent["event"], "session.status")
        self.assertEqual(sent["data"]["status"], "paused")
        self.assertEqual(sent["event_version"], "2")

    def test_pause_unknown_connection(self):
        from deskai.handlers.websocket.session_pause_handler import (
            handle_session_pause,
        )

        self.connection_repo.find_by_connection_id.return_value = None

        result = handle_session_pause(
            self._make_event(),
            self.connection_repo,
            self.pause_use_case,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 400)


class SessionResumeHandlerTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.resume_use_case = MagicMock()
        self.apigw = MagicMock()

    def _make_event(self):
        return {
            "requestContext": {"connectionId": "conn-abc"},
            "body": json.dumps({
                "action": "session.resume",
                "data": {
                    "consultation_id": "cons-001",
                    "timestamp": "2026-04-02T10:10:00+00:00",
                },
            }),
        }

    def test_resume_success(self):
        from deskai.handlers.websocket.session_resume_handler import (
            handle_session_resume,
        )

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        self.resume_use_case.execute.return_value = _make_session(state=SessionState.RECORDING)

        result = handle_session_resume(
            self._make_event(),
            self.connection_repo,
            self.resume_use_case,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 200)
        self.resume_use_case.execute.assert_called_once()
        self.apigw.send_to_connection.assert_called_once()
        sent = self.apigw.send_to_connection.call_args[1]["data"]
        self.assertEqual(sent["event"], "session.status")
        self.assertEqual(sent["data"]["status"], "recording")
        self.assertEqual(sent["event_version"], "2")


if __name__ == "__main__":
    unittest.main()
