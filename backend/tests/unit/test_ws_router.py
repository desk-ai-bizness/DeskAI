"""Unit tests for the WebSocket Lambda router."""

import json
import unittest
from unittest.mock import MagicMock, patch

_ROUTER = "deskai.handlers.websocket.router"


def _noop():
    return MagicMock()


class WebSocketRouterTest(unittest.TestCase):
    """Test that the Lambda entry point routes events to the correct handler."""

    def _make_connect_event(self):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$connect",
            },
            "queryStringParameters": {"token": "valid-token"},
        }

    def _make_disconnect_event(self):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$disconnect",
            },
        }

    def _make_default_event(self, action, data=None):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$default",
            },
            "body": json.dumps({"action": action, "data": data or {}}),
        }

    @patch(f"{_ROUTER}._get_auth_provider", new=_noop)
    @patch(f"{_ROUTER}._get_connection_repo", new=_noop)
    @patch("deskai.handlers.websocket.connect_handler.handle_connect")
    def test_route_connect(self, mock_handler):
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        event = self._make_connect_event()

        result = handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._get_session_repo", new=_noop)
    @patch(f"{_ROUTER}._get_connection_repo", new=_noop)
    @patch("deskai.handlers.websocket.disconnect_handler.handle_disconnect")
    def test_route_disconnect(self, mock_handler):
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        event = self._make_disconnect_event()

        result = handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._get_apigw", new=_noop)
    @patch(f"{_ROUTER}._get_session_repo", new=_noop)
    @patch(f"{_ROUTER}._get_connection_repo", new=_noop)
    @patch("deskai.handlers.websocket.session_init_handler.handle_session_init")
    def test_route_session_init(self, mock_handler):
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        event = self._make_default_event("session.init")

        result = handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._get_transcription_provider", new=_noop)
    @patch(f"{_ROUTER}._get_apigw", new=_noop)
    @patch(f"{_ROUTER}._get_session_repo", new=_noop)
    @patch(f"{_ROUTER}._get_connection_repo", new=_noop)
    @patch("deskai.handlers.websocket.audio_chunk_handler.handle_audio_chunk")
    def test_route_audio_chunk(self, mock_handler):
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        event = self._make_default_event("audio.chunk")

        result = handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._get_finalize_transcript_use_case", new=_noop)
    @patch(f"{_ROUTER}._get_apigw", new=_noop)
    @patch(f"{_ROUTER}._get_end_session_use_case", new=_noop)
    @patch(f"{_ROUTER}._get_connection_repo", new=_noop)
    @patch("deskai.handlers.websocket.session_stop_handler.handle_session_stop")
    def test_route_session_stop(self, mock_handler):
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        event = self._make_default_event("session.stop")

        result = handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch("deskai.handlers.websocket.ping_handler.handle_ping")
    def test_route_client_ping(self, mock_handler):
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        event = self._make_default_event("client.ping")

        result = handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    def test_route_unknown_action(self):
        from deskai.handlers.websocket.router import handler

        event = self._make_default_event("unknown.action")

        result = handler(event, None)

        self.assertEqual(result["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
