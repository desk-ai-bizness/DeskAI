"""Unit tests for the WebSocket audio chunk handler."""

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


def _make_session(state=SessionState.RECORDING, chunks=5, **overrides):
    defaults = dict(
        session_id="sess-001",
        consultation_id="cons-001",
        doctor_id="doc-001",
        clinic_id="clinic-001",
        state=state,
        started_at="2026-04-02T10:00:00+00:00",
        audio_chunks_received=chunks,
    )
    defaults.update(overrides)
    return Session(**defaults)


class HandleAudioChunkTest(unittest.TestCase):
    def setUp(self):
        self.connection_repo = MagicMock()
        self.session_repo = MagicMock()
        self.apigw = MagicMock()

    def _make_event(self, chunk_index=0, audio="dGVzdA==", timestamp="2026-04-02T12:00:00+00:00"):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$default",
            },
            "body": json.dumps(
                {
                    "action": "audio.chunk",
                    "data": {
                        "chunk_index": chunk_index,
                        "audio": audio,
                        "timestamp": timestamp,
                    },
                }
            ),
        }

    @patch(
        "deskai.handlers.websocket.audio_chunk_handler.utc_now_iso",
        return_value="2026-04-02T12:00:00+00:00",
    )
    def test_chunk_accepted(self, _mock_time):
        from deskai.handlers.websocket.audio_chunk_handler import handle_audio_chunk

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        session = _make_session(state=SessionState.RECORDING, chunks=5)
        self.session_repo.find_by_id.return_value = session

        result = handle_audio_chunk(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 200)
        self.session_repo.update.assert_called_once()
        updated = self.session_repo.update.call_args[0][0]
        self.assertEqual(updated.audio_chunks_received, 6)
        self.assertEqual(updated.last_activity_at, "2026-04-02T12:00:00+00:00")
        self.apigw.send_to_connection.assert_called_once()
        sent = self.apigw.send_to_connection.call_args[1]["data"]
        self.assertEqual(sent["event"], "transcript.partial")
        self.assertFalse(sent["data"]["is_final"])

    def test_chunk_rejected_not_recording(self):
        from deskai.handlers.websocket.audio_chunk_handler import handle_audio_chunk

        self.connection_repo.find_by_connection_id.return_value = _make_connection()
        session = _make_session(state=SessionState.ENDED)
        self.session_repo.find_by_id.return_value = session

        result = handle_audio_chunk(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 400)
        self.session_repo.update.assert_not_called()

    def test_chunk_unknown_connection(self):
        from deskai.handlers.websocket.audio_chunk_handler import handle_audio_chunk

        self.connection_repo.find_by_connection_id.return_value = None

        result = handle_audio_chunk(
            self._make_event(),
            self.connection_repo,
            self.session_repo,
            self.apigw,
        )

        self.assertEqual(result["statusCode"], 400)
        self.session_repo.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
