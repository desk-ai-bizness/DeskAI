"""Tests for middleware logging behavior.

Verifies that ``handle_domain_errors`` emits structured logs at the
correct levels with the correct context fields.
"""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.auth.exceptions import AuthenticationError
from deskai.domain.consultation.exceptions import ConsultationNotFoundError
from deskai.handlers.http.middleware import handle_domain_errors


class HandleDomainErrorsLoggingTest(unittest.TestCase):
    """Verify the decorator emits request/response and error logs."""

    def _make_event(
        self,
        method: str = "GET",
        path: str = "/v1/consultations",
        request_id: str = "req-001",
    ) -> dict:
        return {
            "requestContext": {
                "http": {"method": method, "path": path},
                "requestId": request_id,
            },
        }

    # --- Successful request ---

    @patch("deskai.handlers.http.middleware.logger")
    def test_success_emits_received_and_completed(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            return {"statusCode": 200, "body": "{}"}

        handler(self._make_event())

        events = [c.args[0] for c in mock_logger.info.call_args_list]
        self.assertIn("http_request_received", events)
        self.assertIn("http_request_completed", events)

    @patch("deskai.handlers.http.middleware.logger")
    def test_completed_log_contains_structured_fields(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            return {"statusCode": 201, "body": "{}"}

        handler(self._make_event(method="POST", path="/v1/patients", request_id="req-42"))

        completed_call = next(
            c for c in mock_logger.info.call_args_list
            if c.args[0] == "http_request_completed"
        )
        extra = completed_call.kwargs.get("extra", {})
        self.assertEqual(extra["http_method"], "POST")
        self.assertEqual(extra["http_path"], "/v1/patients")
        self.assertEqual(extra["http_status"], 201)
        self.assertEqual(extra["request_id"], "req-42")
        self.assertIn("duration_ms", extra)
        self.assertIsInstance(extra["duration_ms"], int)

    @patch("deskai.handlers.http.middleware.logger")
    def test_received_log_contains_method_and_path(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            return {"statusCode": 200, "body": "{}"}

        handler(self._make_event(method="DELETE", path="/v1/auth/session"))

        received_call = next(
            c for c in mock_logger.info.call_args_list
            if c.args[0] == "http_request_received"
        )
        extra = received_call.kwargs.get("extra", {})
        self.assertEqual(extra["http_method"], "DELETE")
        self.assertEqual(extra["http_path"], "/v1/auth/session")

    # --- Domain errors ---

    @patch("deskai.handlers.http.middleware.logger")
    def test_domain_error_logged_at_warning(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            raise AuthenticationError("bad creds")

        handler(self._make_event())

        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("domain_error", warning_events)

    @patch("deskai.handlers.http.middleware.logger")
    def test_domain_error_contains_error_type_and_code(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            raise ConsultationNotFoundError("not found")

        handler(self._make_event(path="/v1/consultations/c-1"))

        domain_call = next(
            c for c in mock_logger.warning.call_args_list
            if c.args[0] == "domain_error"
        )
        extra = domain_call.kwargs.get("extra", {})
        self.assertEqual(extra["error_type"], "ConsultationNotFoundError")
        self.assertEqual(extra["error_code"], "not_found")
        self.assertEqual(extra["http_status"], 404)
        self.assertIn("duration_ms", extra)

    # --- Unhandled errors ---

    @patch("deskai.handlers.http.middleware.logger")
    def test_unhandled_error_logged_at_error(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            raise RuntimeError("unexpected")

        handler(self._make_event())

        exception_events = [c.args[0] for c in mock_logger.exception.call_args_list]
        self.assertIn("unhandled_error", exception_events)

    @patch("deskai.handlers.http.middleware.logger")
    def test_unhandled_error_contains_500_status(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            raise ValueError("boom")

        handler(self._make_event(path="/v1/sessions"))

        error_call = next(
            c for c in mock_logger.exception.call_args_list
            if c.args[0] == "unhandled_error"
        )
        extra = error_call.kwargs.get("extra", {})
        self.assertEqual(extra["http_status"], 500)
        self.assertEqual(extra["http_path"], "/v1/sessions")
        self.assertIn("duration_ms", extra)

    # --- Duration tracking ---

    @patch("deskai.handlers.http.middleware.logger")
    def test_duration_ms_is_non_negative(
        self, mock_logger: MagicMock,
    ) -> None:
        @handle_domain_errors
        def handler(event):
            return {"statusCode": 200, "body": "{}"}

        handler(self._make_event())

        completed_call = next(
            c for c in mock_logger.info.call_args_list
            if c.args[0] == "http_request_completed"
        )
        self.assertGreaterEqual(completed_call.kwargs["extra"]["duration_ms"], 0)


if __name__ == "__main__":
    unittest.main()
