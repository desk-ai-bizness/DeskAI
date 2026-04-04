"""Tests for WebSocket handler logging behavior.

Verifies that WebSocket handlers emit structured log events at the
correct levels for connection lifecycle and security events.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.value_objects import ConnectionInfo

# ===================================================================
# Connect handler
# ===================================================================


class WsConnectLoggingTest(unittest.TestCase):
    """Verify connect handler emits correct log events."""

    @patch(
        "deskai.handlers.websocket.connect_handler.utc_now_iso",
        return_value="2026-04-03T12:00:00+00:00",
    )
    @patch("deskai.handlers.websocket.connect_handler.logger")
    def test_successful_connect_logs_accepted(
        self, mock_logger: MagicMock, _mock_time: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.connect_handler import handle_connect

        auth_provider = MagicMock()
        auth_provider.validate_ws_token.return_value = {
            "doctor_id": "doc-1",
            "clinic_id": "clinic-1",
        }
        connection_repo = MagicMock()
        event = {
            "requestContext": {"connectionId": "conn-1", "routeKey": "$connect"},
            "queryStringParameters": {"token": "valid"},
        }

        handle_connect(event, connection_repo, auth_provider)

        info_events = [c.args[0] for c in mock_logger.info.call_args_list]
        self.assertIn("ws_connection_accepted", info_events)

        accepted_call = next(
            c for c in mock_logger.info.call_args_list
            if c.args[0] == "ws_connection_accepted"
        )
        extra = accepted_call.kwargs.get("extra", {})
        self.assertEqual(extra["connection_id"], "conn-1")
        self.assertEqual(extra["doctor_id"], "doc-1")

    @patch("deskai.handlers.websocket.connect_handler.logger")
    def test_missing_token_logs_warning(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.connect_handler import handle_connect

        event = {
            "requestContext": {"connectionId": "conn-2", "routeKey": "$connect"},
            "queryStringParameters": None,
        }

        result = handle_connect(event, MagicMock(), MagicMock())

        self.assertEqual(result["statusCode"], 401)
        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("ws_connect_no_token", warning_events)

    @patch("deskai.handlers.websocket.connect_handler.logger")
    def test_invalid_token_logs_auth_failed(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.connect_handler import handle_connect

        auth_provider = MagicMock()
        auth_provider.validate_ws_token.side_effect = ValueError("bad")
        event = {
            "requestContext": {"connectionId": "conn-3", "routeKey": "$connect"},
            "queryStringParameters": {"token": "bad"},
        }

        result = handle_connect(event, MagicMock(), auth_provider)

        self.assertEqual(result["statusCode"], 401)
        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("ws_connect_auth_failed", warning_events)


# ===================================================================
# Session init handler
# ===================================================================


class WsSessionInitLoggingTest(unittest.TestCase):
    """Verify session init handler emits correct log events."""

    def _make_session(self, **kwargs) -> Session:
        defaults = dict(
            session_id="sess-1",
            consultation_id="cons-1",
            doctor_id="doc-1",
            clinic_id="clinic-1",
            state=SessionState.ACTIVE,
            started_at="2026-04-03T10:00:00+00:00",
        )
        defaults.update(kwargs)
        return Session(**defaults)

    def _make_connection(self, **kwargs) -> ConnectionInfo:
        defaults = dict(
            connection_id="conn-1",
            session_id="",
            doctor_id="doc-1",
            clinic_id="clinic-1",
            connected_at="2026-04-03T10:00:00+00:00",
        )
        defaults.update(kwargs)
        return ConnectionInfo(**defaults)

    @patch(
        "deskai.handlers.websocket.session_init_handler.utc_now_iso",
        return_value="2026-04-03T12:00:00+00:00",
    )
    @patch("deskai.handlers.websocket.session_init_handler.logger")
    def test_successful_init_logs_initialized(
        self, mock_logger: MagicMock, _mock_time: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.session_init_handler import (
            handle_session_init,
        )

        connection_repo = MagicMock()
        connection_repo.find_by_connection_id.return_value = self._make_connection()
        session_repo = MagicMock()
        session_repo.find_by_id.return_value = self._make_session()
        apigw = MagicMock()

        event = {
            "requestContext": {"connectionId": "conn-1"},
            "body": json.dumps({
                "event": "session.init",
                "data": {"session_id": "sess-1", "consultation_id": "cons-1"},
            }),
        }

        handle_session_init(event, connection_repo, session_repo, apigw)

        info_events = [c.args[0] for c in mock_logger.info.call_args_list]
        self.assertIn("ws_session_initialized", info_events)

    @patch("deskai.handlers.websocket.session_init_handler.logger")
    def test_unknown_connection_logs_warning(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.session_init_handler import (
            handle_session_init,
        )

        connection_repo = MagicMock()
        connection_repo.find_by_connection_id.return_value = None
        event = {
            "requestContext": {"connectionId": "conn-unknown"},
            "body": json.dumps({
                "event": "session.init",
                "data": {"session_id": "s1"},
            }),
        }

        result = handle_session_init(event, connection_repo, MagicMock(), MagicMock())

        self.assertEqual(result["statusCode"], 400)
        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("ws_session_init_unknown_connection", warning_events)

    @patch("deskai.handlers.websocket.session_init_handler.logger")
    def test_session_not_found_logs_warning(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.session_init_handler import (
            handle_session_init,
        )

        connection_repo = MagicMock()
        connection_repo.find_by_connection_id.return_value = self._make_connection()
        session_repo = MagicMock()
        session_repo.find_by_id.return_value = None
        event = {
            "requestContext": {"connectionId": "conn-1"},
            "body": json.dumps({
                "event": "session.init",
                "data": {"session_id": "missing"},
            }),
        }

        result = handle_session_init(event, connection_repo, session_repo, MagicMock())

        self.assertEqual(result["statusCode"], 400)
        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("ws_session_init_session_not_found", warning_events)

    @patch("deskai.handlers.websocket.session_init_handler.logger")
    def test_ownership_mismatch_logs_warning(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.session_init_handler import (
            handle_session_init,
        )

        connection_repo = MagicMock()
        connection_repo.find_by_connection_id.return_value = self._make_connection(
            doctor_id="doc-other",
        )
        session_repo = MagicMock()
        session_repo.find_by_id.return_value = self._make_session(doctor_id="doc-1")
        event = {
            "requestContext": {"connectionId": "conn-1"},
            "body": json.dumps({
                "event": "session.init",
                "data": {"session_id": "sess-1"},
            }),
        }

        result = handle_session_init(event, connection_repo, session_repo, MagicMock())

        self.assertEqual(result["statusCode"], 403)
        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("ws_session_init_ownership_mismatch", warning_events)


# ===================================================================
# Audio chunk handler
# ===================================================================


class WsAudioChunkLoggingTest(unittest.TestCase):
    """Verify audio chunk handler emits correct log events."""

    @patch("deskai.handlers.websocket.audio_chunk_handler.logger")
    def test_oversized_chunk_logs_warning_with_size(
        self, mock_logger: MagicMock,
    ) -> None:
        import base64

        from deskai.handlers.websocket.audio_chunk_handler import (
            handle_audio_chunk,
        )

        big_audio = base64.b64encode(b"x" * 2_000_000).decode()
        event = {
            "requestContext": {"connectionId": "conn-1"},
            "body": json.dumps({
                "event": "audio.chunk",
                "data": {"audio": big_audio},
            }),
        }

        result = handle_audio_chunk(event, MagicMock(), MagicMock(), MagicMock())

        self.assertEqual(result["statusCode"], 413)
        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("ws_audio_chunk_too_large", warning_events)

        size_call = next(
            c for c in mock_logger.warning.call_args_list
            if c.args[0] == "ws_audio_chunk_too_large"
        )
        extra = size_call.kwargs.get("extra", {})
        self.assertGreater(extra["size_bytes"], 1_000_000)

    @patch("deskai.handlers.websocket.audio_chunk_handler.logger")
    def test_unknown_connection_logs_warning(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.audio_chunk_handler import (
            handle_audio_chunk,
        )

        connection_repo = MagicMock()
        connection_repo.find_by_connection_id.return_value = None
        event = {
            "requestContext": {"connectionId": "conn-ghost"},
            "body": json.dumps({"event": "audio.chunk", "data": {}}),
        }

        result = handle_audio_chunk(event, connection_repo, MagicMock(), MagicMock())

        self.assertEqual(result["statusCode"], 400)
        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("ws_audio_chunk_unknown_connection", warning_events)

    @patch("deskai.handlers.websocket.audio_chunk_handler.logger")
    def test_successful_chunk_logs_at_debug(
        self, mock_logger: MagicMock,
    ) -> None:
        import base64

        from deskai.handlers.websocket.audio_chunk_handler import (
            handle_audio_chunk,
        )

        audio = base64.b64encode(b"tiny-audio").decode()
        connection = ConnectionInfo(
            connection_id="conn-1", session_id="sess-1",
            doctor_id="doc-1", clinic_id="clinic-1",
            connected_at="2026-04-03T10:00:00+00:00",
        )
        session = Session(
            session_id="sess-1", consultation_id="cons-1",
            doctor_id="doc-1", clinic_id="clinic-1",
            state=SessionState.RECORDING,
            audio_chunks_received=0,
            started_at="2026-04-03T10:00:00+00:00",
            last_activity_at="2026-04-03T10:00:00+00:00",
        )

        connection_repo = MagicMock()
        connection_repo.find_by_connection_id.return_value = connection
        session_repo = MagicMock()
        session_repo.find_by_id.return_value = session
        apigw = MagicMock()

        event = {
            "requestContext": {"connectionId": "conn-1"},
            "body": json.dumps({"event": "audio.chunk", "data": {"audio": audio}}),
        }

        handle_audio_chunk(event, connection_repo, session_repo, apigw)

        debug_events = [c.args[0] for c in mock_logger.debug.call_args_list]
        self.assertIn("ws_audio_chunk_processed", debug_events)


if __name__ == "__main__":
    unittest.main()
