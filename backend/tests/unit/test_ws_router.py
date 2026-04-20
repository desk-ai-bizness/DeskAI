"""Unit tests for the WebSocket Lambda router."""

import json
import unittest
from unittest.mock import MagicMock, patch

_ROUTER = "deskai.handlers.websocket.router"


def _mock_container():
    """Return a MagicMock container with all required attributes."""
    c = MagicMock()
    c.connection_repo = MagicMock()
    c.session_repo = MagicMock()
    c.auth_provider = MagicMock()
    c.transcription_provider = MagicMock()
    c.end_session = MagicMock()
    c.transcript_segment_repo = MagicMock()
    c.pause_session = MagicMock()
    c.resume_session = MagicMock()
    return c


class WebSocketRouterTest(unittest.TestCase):
    """Test that the Lambda entry point routes events to the correct handler."""

    def setUp(self) -> None:
        self.container = _mock_container()
        self.apigw = MagicMock()

    def _make_connect_event(self):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$connect",
                "domainName": "test.execute-api.us-east-1.amazonaws.com",
                "stage": "dev",
            },
            "queryStringParameters": {"token": "valid-token"},
        }

    def _make_disconnect_event(self):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$disconnect",
                "domainName": "test.execute-api.us-east-1.amazonaws.com",
                "stage": "dev",
            },
        }

    def _make_default_event(self, action, data=None):
        return {
            "requestContext": {
                "connectionId": "conn-abc",
                "routeKey": "$default",
                "domainName": "test.execute-api.us-east-1.amazonaws.com",
                "stage": "dev",
            },
            "body": json.dumps({"action": action, "data": data or {}}),
        }

    @patch(f"{_ROUTER}._get_container")
    @patch("deskai.handlers.websocket.connect_handler.handle_connect")
    def test_route_connect(self, mock_handler, mock_get_container):
        mock_get_container.return_value = self.container
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        result = handler(self._make_connect_event(), None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._get_container")
    @patch("deskai.handlers.websocket.disconnect_handler.handle_disconnect")
    def test_route_disconnect(self, mock_handler, mock_get_container):
        mock_get_container.return_value = self.container
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        result = handler(self._make_disconnect_event(), None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._build_apigw")
    @patch(f"{_ROUTER}._get_container")
    @patch("deskai.handlers.websocket.session_init_handler.handle_session_init")
    def test_route_session_init(self, mock_handler, mock_get_container, mock_apigw):
        mock_get_container.return_value = self.container
        mock_apigw.return_value = self.apigw
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        result = handler(self._make_default_event("session.init"), None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._build_apigw")
    @patch(f"{_ROUTER}._get_container")
    @patch("deskai.handlers.websocket.transcript_commit_handler.handle_transcript_commit")
    def test_route_transcript_commit(self, mock_handler, mock_get_container, mock_apigw):
        mock_get_container.return_value = self.container
        mock_apigw.return_value = self.apigw
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        result = handler(self._make_default_event("transcript.commit"), None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._build_apigw")
    @patch(f"{_ROUTER}._get_container")
    @patch("deskai.handlers.websocket.session_pause_handler.handle_session_pause")
    def test_route_session_pause(self, mock_handler, mock_get_container, mock_apigw):
        mock_get_container.return_value = self.container
        mock_apigw.return_value = self.apigw
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        result = handler(self._make_default_event("session.pause"), None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._build_apigw")
    @patch(f"{_ROUTER}._get_container")
    @patch("deskai.handlers.websocket.session_resume_handler.handle_session_resume")
    def test_route_session_resume(self, mock_handler, mock_get_container, mock_apigw):
        mock_get_container.return_value = self.container
        mock_apigw.return_value = self.apigw
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        result = handler(self._make_default_event("session.resume"), None)

        self.assertEqual(result["statusCode"], 200)
        mock_handler.assert_called_once()

    @patch(f"{_ROUTER}._build_apigw")
    @patch(f"{_ROUTER}._get_container")
    @patch("deskai.handlers.websocket.session_stop_handler.handle_session_stop")
    def test_route_session_stop(self, mock_handler, mock_get_container, mock_apigw):
        mock_get_container.return_value = self.container
        mock_apigw.return_value = self.apigw
        from deskai.handlers.websocket.router import handler

        mock_handler.return_value = {"statusCode": 200}
        result = handler(self._make_default_event("session.stop"), None)

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
