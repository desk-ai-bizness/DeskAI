"""Unit tests for the WebSocket Lambda handler entry point."""

import unittest
from unittest.mock import MagicMock, patch


class WebSocketLambdaHandlerTest(unittest.TestCase):
    """Tests for infra/lambda_handlers/websocket.handler."""

    def _import_handler(self):
        import sys
        import types
        from pathlib import Path

        repo_root = str(Path(__file__).resolve().parents[3])
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        if "infra" not in sys.modules:
            pkg = types.ModuleType("infra")
            pkg.__path__ = [str(Path(repo_root) / "infra")]
            sys.modules["infra"] = pkg

        from infra.lambda_handlers.websocket import handler

        return handler

    @patch("deskai.handlers.websocket.router.handler")
    def test_delegates_to_backend_ws_router(
        self, mock_ws_handler: MagicMock
    ) -> None:
        mock_ws_handler.return_value = {"statusCode": 200}
        handler = self._import_handler()
        event = {"requestContext": {"routeKey": "$connect"}}
        ctx = MagicMock()

        result = handler(event, ctx)

        mock_ws_handler.assert_called_once_with(event, ctx)
        self.assertEqual(result["statusCode"], 200)

    @patch("deskai.handlers.websocket.router.handler")
    def test_passes_event_and_context_through(
        self, mock_ws_handler: MagicMock
    ) -> None:
        mock_ws_handler.return_value = {"statusCode": 200}
        handler = self._import_handler()

        event = {"requestContext": {"routeKey": "$disconnect"}}
        ctx = MagicMock(aws_request_id="req-ws-001")

        handler(event, ctx)

        call_args = mock_ws_handler.call_args
        self.assertIs(call_args[0][0], event)
        self.assertIs(call_args[0][1], ctx)


if __name__ == "__main__":
    unittest.main()
