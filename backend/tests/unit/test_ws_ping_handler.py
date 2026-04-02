"""Unit tests for the WebSocket ping handler."""

import unittest
from unittest.mock import patch


class HandlePingTest(unittest.TestCase):
    @patch(
        "deskai.handlers.websocket.ping_handler.utc_now_iso",
        return_value="2026-04-02T12:00:00+00:00",
    )
    def test_ping_returns_pong_with_timestamp(self, _mock_time):
        from deskai.handlers.websocket.ping_handler import handle_ping

        event = {
            "requestContext": {"connectionId": "conn-123", "routeKey": "$default"},
            "body": '{"action": "client.ping"}',
        }

        result = handle_ping(event)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(
            result["body"],
            {
                "event": "server.pong",
                "data": {"timestamp": "2026-04-02T12:00:00+00:00"},
            },
        )


if __name__ == "__main__":
    unittest.main()
