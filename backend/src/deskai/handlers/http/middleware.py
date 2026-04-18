"""HTTP handler middleware for auth context extraction and error mapping."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from deskai.application.auth.get_current_user import (
    GetCurrentUserUseCase,
)
from deskai.domain.auth.exceptions import (
    AccountDisabledError,
    AccountNotVerifiedError,
    AuthenticationError,
    DoctorProfileNotFoundError,
    PlanLimitExceededError,
    TrialExpiredError,
    UnauthorizedAccessError,
)
from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.exceptions import (
    ConsultationAlreadyFinalizedError,
    ConsultationNotFoundError,
    ConsultationOwnershipError,
    InvalidStatusTransitionError,
)
from deskai.domain.export.exceptions import ExportGenerationError
from deskai.domain.patient.exceptions import (
    PatientDuplicateCpfError,
    PatientNotFoundError,
    PatientValidationError,
)
from deskai.domain.review.exceptions import (
    ArtifactsIncompleteError,
    ExportNotAllowedError,
    FinalizationNotAllowedError,
    ReviewNotAvailableError,
    ReviewNotEditableError,
)
from deskai.domain.session.exceptions import (
    InvalidSessionStateError,
    SessionNotActiveError,
    SessionOwnershipError,
)
from deskai.shared.logging import get_logger, log_context

logger = get_logger()

_EXCEPTION_MAP: dict[type[Exception], tuple[int, str]] = {
    AuthenticationError: (401, "unauthorized"),
    AccountNotVerifiedError: (401, "account_not_verified"),
    AccountDisabledError: (403, "forbidden"),
    DoctorProfileNotFoundError: (403, "forbidden"),
    UnauthorizedAccessError: (403, "forbidden"),
    PlanLimitExceededError: (403, "plan_limit_exceeded"),
    TrialExpiredError: (403, "trial_expired"),
    ConsultationNotFoundError: (404, "not_found"),
    ConsultationOwnershipError: (403, "forbidden"),
    InvalidStatusTransitionError: (409, "conflict"),
    ConsultationAlreadyFinalizedError: (409, "conflict"),
    PatientNotFoundError: (404, "not_found"),
    PatientValidationError: (400, "validation_error"),
    PatientDuplicateCpfError: (409, "conflict"),
    InvalidSessionStateError: (409, "conflict"),
    SessionNotActiveError: (404, "not_found"),
    SessionOwnershipError: (403, "forbidden"),
    ReviewNotAvailableError: (409, "conflict"),
    ReviewNotEditableError: (409, "conflict"),
    FinalizationNotAllowedError: (409, "conflict"),
    ExportNotAllowedError: (409, "conflict"),
    ArtifactsIncompleteError: (409, "conflict"),
    ExportGenerationError: (500, "internal_error"),
}


def extract_auth_context(
    event: dict[str, Any],
    get_current_user: GetCurrentUserUseCase,
) -> AuthContext:
    """Build an AuthContext from API Gateway JWT authorizer claims."""
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    identity_provider_id = claims.get("sub")
    email = claims.get("email", "")

    if not identity_provider_id:
        raise AuthenticationError("Missing user identity in request.")

    profile = get_current_user.execute(identity_provider_id)
    return AuthContext(
        doctor_id=profile.doctor_id,
        email=email or profile.email,
        clinic_id=profile.clinic_id,
        plan_type=profile.plan_type,
    )


def error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standard error response envelope."""
    body: dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    if details:
        body["error"]["details"] = details
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def json_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Build a standard JSON success response."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def no_content_response() -> dict[str, Any]:
    """Build a 204 No Content response."""
    return {"statusCode": 204, "headers": {}}


def parse_json_body(event: dict[str, Any]) -> dict[str, Any]:
    """Parse the JSON body from an API Gateway v2 event.

    API Gateway HTTP API v2 may inject invalid backslash escapes (e.g. ``\\!``)
    into the body string.  We strip those before parsing so that ``json.loads``
    does not silently fail.
    """
    import base64
    import re

    raw = event.get("body", "")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    # Remove invalid JSON backslash escapes injected by API Gateway.
    # Valid JSON escapes: \" \\ \/ \b \f \n \r \t \uXXXX
    raw = re.sub(r'\\(?!["\\/bfnrtu])', "", raw)
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("json_parse_error", extra=log_context(body_length=len(raw)))
        return {}


def handle_domain_errors(
    fn: Callable[..., dict[str, Any]],
) -> Callable[..., dict[str, Any]]:
    """Decorator that maps domain exceptions to HTTP error responses."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        event = args[0] if args else {}
        http_ctx = event.get("requestContext", {}).get("http", {})
        method = http_ctx.get("method", "")
        path = http_ctx.get("path", "")
        request_id = event.get("requestContext", {}).get("requestId", "")

        logger.info(
            "http_request_received",
            extra=log_context(
                http_method=method,
                http_path=path,
                request_id=request_id,
            ),
        )

        start = time.monotonic()
        try:
            result = fn(*args, **kwargs)
            duration_ms = int((time.monotonic() - start) * 1000)
            status_code = result.get("statusCode", 0)
            logger.info(
                "http_request_completed",
                extra=log_context(
                    http_method=method,
                    http_path=path,
                    http_status=status_code,
                    duration_ms=duration_ms,
                    request_id=request_id,
                ),
            )
            return result
        except tuple(_EXCEPTION_MAP) as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            status_code, code = next(
                (sc, c) for cls, (sc, c) in _EXCEPTION_MAP.items() if isinstance(exc, cls)
            )
            logger.warning(
                "domain_error",
                extra=log_context(
                    error_code=code,
                    error_type=type(exc).__name__,
                    http_method=method,
                    http_path=path,
                    http_status=status_code,
                    duration_ms=duration_ms,
                    request_id=request_id,
                ),
            )
            return error_response(status_code, code, str(exc))
        except Exception:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.exception(
                "unhandled_error",
                extra=log_context(
                    http_method=method,
                    http_path=path,
                    http_status=500,
                    duration_ms=duration_ms,
                    request_id=request_id,
                ),
            )
            return error_response(
                500,
                "internal_error",
                "Ocorreu um erro inesperado. Tente novamente.",
            )

    return wrapper
