"""Unit tests for the BFF Lambda router."""

import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# The bff.py handler lives under infra/lambda_handlers/ which is outside
# the backend package.  Add the repo root so ``infra`` is importable.
_REPO_ROOT = str(
    Path(__file__).resolve().parents[3]
)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Create the ``infra`` package in sys.modules if it doesn't exist
# (the directory has no __init__.py at the top level).
if "infra" not in sys.modules:
    _infra_pkg = types.ModuleType("infra")
    _infra_pkg.__path__ = [
        str(Path(_REPO_ROOT) / "infra")
    ]
    sys.modules["infra"] = _infra_pkg

from infra.lambda_handlers.bff import handler  # noqa: E402


def _api_event(
    path: str = "/", method: str = "GET", body: str = ""
) -> dict:
    event: dict = {
        "rawPath": path,
        "requestContext": {
            "http": {"method": method}
        },
        "headers": {},
    }
    if body:
        event["body"] = body
    return event


class BffRouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.patcher = patch(
            "infra.lambda_handlers.bff._get_container",
            return_value=self.container,
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_health_endpoint(self) -> None:
        ctx = MagicMock()
        ctx.aws_request_id = "req-1"
        resp = handler(
            _api_event("/health", "GET"), ctx
        )

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["request_id"], "req-1")

    @patch(
        "deskai.handlers.http.auth_handler.handle_login"
    )
    def test_login_route(
        self, mock_login: MagicMock
    ) -> None:
        mock_login.return_value = {
            "statusCode": 200,
            "body": "{}",
        }
        event = _api_event(
            "/v1/auth/session", "POST"
        )
        handler(event, MagicMock())

        mock_login.assert_called_once_with(
            event, self.container
        )

    @patch(
        "deskai.handlers.http.auth_handler.handle_logout"
    )
    def test_logout_route(
        self, mock_logout: MagicMock
    ) -> None:
        mock_logout.return_value = {
            "statusCode": 204,
        }
        event = _api_event(
            "/v1/auth/session", "DELETE"
        )
        handler(event, MagicMock())

        mock_logout.assert_called_once_with(
            event, self.container
        )

    @patch(
        "deskai.handlers.http.me_handler.handle_get_me"
    )
    def test_me_route(
        self, mock_get_me: MagicMock
    ) -> None:
        mock_get_me.return_value = {
            "statusCode": 200,
            "body": "{}",
        }
        event = _api_event("/v1/me", "GET")
        handler(event, MagicMock())

        mock_get_me.assert_called_once_with(
            event, self.container
        )

    def test_unknown_route_returns_404(self) -> None:
        resp = handler(
            _api_event("/v1/unknown", "GET"),
            MagicMock(),
        )

        self.assertEqual(resp["statusCode"], 404)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "not_found")

    def test_stage_prefix_stripped(self) -> None:
        ctx = MagicMock()
        ctx.aws_request_id = "req-2"
        resp = handler(
            _api_event("/dev/health", "GET"), ctx
        )

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
