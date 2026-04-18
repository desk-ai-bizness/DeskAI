"""PII safety tests — verify sensitive data never leaks into log output.

For a healthcare application, logging PII (patient names, DOB, emails,
passwords, tokens, raw transcripts) is a compliance violation.  These
tests exercise the real handler/middleware code paths and inspect every
``logger.*`` call to ensure no forbidden field appears.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.auth.value_objects import Tokens
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.value_objects import ConnectionInfo

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Fields that must NEVER appear in a log ``extra`` dict.
_PII_KEYS = frozenset({
    "password",
    "new_password",
    "token",
    "access_token",
    "refresh_token",
    "email",
    "patient_name",
    "name",
    "cpf",
    "date_of_birth",
    "dob",
    "raw_transcript",
    "transcript_text",
    "audio",
    "audio_data",
    "body_preview",
})


def _collect_log_extras(mock_logger: MagicMock) -> list[dict]:
    """Extract all ``extra`` dicts passed to any log-level call."""
    extras: list[dict] = []
    for method_name in ("debug", "info", "warning", "error", "exception"):
        method = getattr(mock_logger, method_name)
        for c in method.call_args_list:
            extra = c.kwargs.get("extra") or (
                c.args[1] if len(c.args) > 1 and isinstance(c.args[1], dict) else None
            )
            if extra is not None:
                extras.append(extra)
    return extras


def _assert_no_pii_in_extras(
    test_case: unittest.TestCase,
    extras: list[dict],
) -> None:
    """Fail if any extra dict contains a PII key."""
    for extra in extras:
        leaked = _PII_KEYS & set(extra.keys())
        test_case.assertEqual(
            leaked,
            set(),
            f"PII keys leaked into log: {leaked} in {extra}",
        )


def _assert_value_not_in_extras(
    test_case: unittest.TestCase,
    extras: list[dict],
    value: str,
    label: str = "sensitive value",
) -> None:
    """Fail if *value* appears as any dict value (string match)."""
    for extra in extras:
        for k, v in extra.items():
            if isinstance(v, str) and value in v:
                test_case.fail(
                    f"{label} '{value}' leaked in log field "
                    f"'{k}': '{v}'"
                )


# ===================================================================
# 1. Middleware — parse_json_body must not log body content
# ===================================================================


class MiddlewarePiiSafetyTest(unittest.TestCase):
    """Verify parse_json_body never leaks request body content."""

    @patch("deskai.handlers.http.middleware.logger")
    def test_parse_json_body_does_not_log_body_content(
        self, mock_logger: MagicMock,
    ) -> None:
        """A malformed body triggers a warning, but the body itself is not logged."""
        from deskai.handlers.http.middleware import parse_json_body

        parse_json_body({"body": "not-json-with-secret-password"})

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        _assert_value_not_in_extras(
            self, extras, "secret-password", "body content",
        )

    @patch("deskai.handlers.http.middleware.logger")
    def test_parse_json_body_logs_length_not_content(
        self, mock_logger: MagicMock,
    ) -> None:
        """On parse failure, only the body *length* should be logged."""
        from deskai.handlers.http.middleware import parse_json_body

        raw = "this is invalid json containing PII like dr.smith@hospital.com"
        parse_json_body({"body": raw})

        extras = _collect_log_extras(mock_logger)
        # Must contain body_length
        logged_lengths = [e.get("body_length") for e in extras if "body_length" in e]
        self.assertTrue(
            any(length == len(raw) for length in logged_lengths),
            f"Expected body_length={len(raw)} in extras, got {extras}",
        )
        # Must NOT contain body_preview or body content
        _assert_no_pii_in_extras(self, extras)


# ===================================================================
# 2. Auth handlers — passwords, tokens, emails must not be logged
# ===================================================================


class AuthHandlerPiiSafetyTest(unittest.TestCase):
    """Verify auth handler log calls never contain credentials or PII.

    Uses ``assertLogs`` to capture log records at the logging-framework
    level, avoiding module-path sensitivity with ``@patch``.
    """

    _LOGGER_NAME = "deskai-backend"

    def setUp(self) -> None:
        self.container = MagicMock()

    @staticmethod
    def _records_extra_dicts(records) -> list[dict]:
        """Extract structured extras from captured LogRecords.

        AWS Lambda Powertools Logger injects ``extra`` values as
        top-level record attributes.  We check every attribute that
        is not part of the standard LogRecord set.
        """
        import logging

        standard = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)
        extras: list[dict] = []
        for r in records:
            extra = {k: v for k, v in r.__dict__.items() if k not in standard}
            if extra:
                extras.append(extra)
        return extras

    def _assert_no_pii_in_records(self, records) -> None:
        """Fail if any captured log record contains PII in messages or extras."""
        extras = self._records_extra_dicts(records)
        _assert_no_pii_in_extras(self, extras)

        # Also check that the log *message* strings don't contain PII values
        for r in records:
            msg = r.getMessage()
            for _pii_key in _PII_KEYS:
                # Message should not contain the PII key name as a field
                # (heuristic: check that common sensitive values aren't embedded)
                self.assertNotIn(
                    "password=", msg,
                    f"PII value found in log message: {msg}",
                )

    def _assert_values_absent_from_records(
        self, records, values: dict[str, str],
    ) -> None:
        """Fail if any of *values* appear in log messages or extras."""
        extras = self._records_extra_dicts(records)
        for label, val in values.items():
            _assert_value_not_in_extras(self, extras, val, label)
            for r in records:
                self.assertNotIn(
                    val, r.getMessage(),
                    f"{label} '{val}' leaked in log message",
                )

    def test_login_does_not_log_password_or_email(self) -> None:
        from deskai.handlers.http.auth_handler import handle_login

        self.container.authenticate.execute.return_value = Tokens(
            access_token="secret-at",
            refresh_token="secret-rt",
            expires_in=3600,
        )
        event = {"body": json.dumps({
            "email": "patient@hospital.com",
            "password": "SuperSecret123!",
        })}

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            handle_login(event, self.container)

        self._assert_no_pii_in_records(cm.records)
        self._assert_values_absent_from_records(cm.records, {
            "password": "SuperSecret123!",
            "email": "patient@hospital.com",
            "access_token": "secret-at",
            "refresh_token": "secret-rt",
        })

    def test_logout_does_not_log_bearer_token(self) -> None:
        from deskai.handlers.http.auth_handler import handle_logout

        event = {"headers": {"authorization": "Bearer my-jwt-token-xyz"}}

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            handle_logout(event, self.container)

        self._assert_no_pii_in_records(cm.records)
        self._assert_values_absent_from_records(cm.records, {
            "bearer token": "my-jwt-token-xyz",
        })

    def test_forgot_password_does_not_log_email(self) -> None:
        from deskai.handlers.http.auth_handler import handle_forgot_password

        event = {"body": json.dumps({"email": "victim@example.com"})}

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            handle_forgot_password(event, self.container)

        self._assert_no_pii_in_records(cm.records)
        self._assert_values_absent_from_records(cm.records, {
            "email": "victim@example.com",
        })

    def test_confirm_forgot_password_does_not_log_credentials(self) -> None:
        from deskai.handlers.http.auth_handler import handle_confirm_forgot_password

        event = {"body": json.dumps({
            "email": "user@test.com",
            "confirmation_code": "123456",
            "new_password": "MyNewPass!99",
        })}

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            handle_confirm_forgot_password(event, self.container)

        self._assert_no_pii_in_records(cm.records)
        self._assert_values_absent_from_records(cm.records, {
            "new_password": "MyNewPass!99",
            "email": "user@test.com",
            "confirmation_code": "123456",
        })


# ===================================================================
# 3. Middleware decorator — domain errors must not leak PII
# ===================================================================


class MiddlewareDecoratorPiiSafetyTest(unittest.TestCase):
    """Verify handle_domain_errors never leaks request body or error details containing PII."""

    @patch("deskai.handlers.http.middleware.logger")
    def test_successful_request_logs_no_pii(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.http.middleware import handle_domain_errors

        @handle_domain_errors
        def handler(event):
            return {"statusCode": 200, "body": "{}"}

        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/v1/auth/session"},
                "requestId": "req-123",
            },
            "body": json.dumps({
                "email": "secret@email.com",
                "password": "P@ssw0rd!",
            }),
        }
        handler(event)

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        _assert_value_not_in_extras(self, extras, "secret@email.com", "email")
        _assert_value_not_in_extras(self, extras, "P@ssw0rd!", "password")

    @patch("deskai.handlers.http.middleware.logger")
    def test_domain_error_warning_logs_no_pii(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.domain.auth.exceptions import AuthenticationError
        from deskai.handlers.http.middleware import handle_domain_errors

        @handle_domain_errors
        def handler(event):
            raise AuthenticationError("Invalid credentials for dr@clinic.com")

        event = {
            "requestContext": {
                "http": {"method": "POST", "path": "/v1/auth/session"},
                "requestId": "req-456",
            },
        }
        handler(event)

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        # The error_type and error_code are safe, but the email in the
        # exception message must NOT be in structured extras.
        _assert_value_not_in_extras(self, extras, "dr@clinic.com", "email in error")

    @patch("deskai.handlers.http.middleware.logger")
    def test_unhandled_error_logs_no_pii_in_extras(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.http.middleware import handle_domain_errors

        @handle_domain_errors
        def handler(event):
            raise RuntimeError("DB error for patient John Doe")

        event = {
            "requestContext": {
                "http": {"method": "GET", "path": "/v1/consultations"},
                "requestId": "req-789",
            },
        }
        handler(event)

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        _assert_value_not_in_extras(self, extras, "John Doe", "patient name")


# ===================================================================
# 4. WebSocket connect — token must not be logged
# ===================================================================


class WsConnectPiiSafetyTest(unittest.TestCase):
    """Verify WebSocket connect handler never logs auth tokens."""

    @patch(
        "deskai.handlers.websocket.connect_handler.utc_now_iso",
        return_value="2026-04-03T12:00:00+00:00",
    )
    @patch("deskai.handlers.websocket.connect_handler.logger")
    def test_successful_connect_does_not_log_token(
        self, mock_logger: MagicMock, _mock_time: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.connect_handler import handle_connect

        auth_provider = MagicMock()
        auth_provider.validate_ws_token.return_value = {
            "doctor_id": "doc-001",
            "clinic_id": "clinic-001",
        }
        connection_repo = MagicMock()

        event = {
            "requestContext": {"connectionId": "conn-1", "routeKey": "$connect"},
            "queryStringParameters": {"token": "super-secret-jwt"},
        }
        handle_connect(event, connection_repo, auth_provider)

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        _assert_value_not_in_extras(self, extras, "super-secret-jwt", "ws token")

    @patch("deskai.handlers.websocket.connect_handler.logger")
    def test_failed_connect_does_not_log_token(
        self, mock_logger: MagicMock,
    ) -> None:
        from deskai.handlers.websocket.connect_handler import handle_connect

        auth_provider = MagicMock()
        auth_provider.validate_ws_token.side_effect = ValueError("bad")
        connection_repo = MagicMock()

        event = {
            "requestContext": {"connectionId": "conn-2", "routeKey": "$connect"},
            "queryStringParameters": {"token": "expired-jwt-token"},
        }
        handle_connect(event, connection_repo, auth_provider)

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        _assert_value_not_in_extras(self, extras, "expired-jwt-token", "ws token")


# ===================================================================
# 5. Audio chunk handler — audio data must not be logged
# ===================================================================


class WsAudioChunkPiiSafetyTest(unittest.TestCase):
    """Verify audio chunk handler never logs audio payload."""

    def _make_session(self, session_id: str = "sess-1") -> Session:
        return Session(
            session_id=session_id,
            consultation_id="cons-1",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.RECORDING,
            audio_chunks_received=0,
            started_at="2026-04-03T12:00:00+00:00",
            last_activity_at="2026-04-03T12:00:00+00:00",
        )

    @patch("deskai.handlers.websocket.audio_chunk_handler.logger")
    def test_audio_chunk_does_not_log_audio_data(
        self, mock_logger: MagicMock,
    ) -> None:
        import base64

        from deskai.handlers.websocket.audio_chunk_handler import (
            handle_audio_chunk,
        )

        audio_payload = base64.b64encode(b"fake-audio-bytes-patient-recording").decode()

        connection = ConnectionInfo(
            connection_id="conn-1",
            session_id="sess-1",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            connected_at="2026-04-03T12:00:00+00:00",
        )
        session = self._make_session()

        connection_repo = MagicMock()
        connection_repo.find_by_connection_id.return_value = connection
        session_repo = MagicMock()
        session_repo.find_by_id.return_value = session
        apigw = MagicMock()

        event = {
            "requestContext": {"connectionId": "conn-1"},
            "body": json.dumps({
                "event": "audio.chunk",
                "data": {"audio": audio_payload},
            }),
        }
        handle_audio_chunk(event, connection_repo, session_repo, apigw)

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        _assert_value_not_in_extras(self, extras, audio_payload, "audio b64")
        _assert_value_not_in_extras(
            self, extras, "fake-audio-bytes", "raw audio",
        )

    @patch("deskai.handlers.websocket.audio_chunk_handler.logger")
    def test_oversized_chunk_does_not_log_audio_data(
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
        handle_audio_chunk(event, MagicMock(), MagicMock(), MagicMock())

        extras = _collect_log_extras(mock_logger)
        _assert_no_pii_in_extras(self, extras)
        # size_bytes is safe (it's a number), but the actual audio must not appear
        _assert_value_not_in_extras(self, extras, big_audio[:50], "audio b64")


if __name__ == "__main__":
    unittest.main()
