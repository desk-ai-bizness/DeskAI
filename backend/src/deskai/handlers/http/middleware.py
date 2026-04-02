"""HTTP handler middleware for auth context extraction and error mapping."""

from __future__ import annotations

import json
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
from deskai.domain.patient.exceptions import (
    PatientNotFoundError,
    PatientValidationError,
)
from deskai.shared.logging import get_logger

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
}


def extract_auth_context(
    event: dict[str, Any],
    get_current_user: GetCurrentUserUseCase,
) -> AuthContext:
    """Build an AuthContext from API Gateway JWT authorizer claims."""
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    cognito_sub = claims.get("sub")
    email = claims.get("email", "")

    if not cognito_sub:
        raise AuthenticationError(
            "Missing user identity in request."
        )

    profile = get_current_user.execute(cognito_sub)
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


def json_response(
    status_code: int, body: dict[str, Any]
) -> dict[str, Any]:
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
    """Parse the JSON body from an API Gateway v2 event."""
    raw = event.get("body", "")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def handle_domain_errors(
    fn: Callable[..., dict[str, Any]],
) -> Callable[..., dict[str, Any]]:
    """Decorator that maps domain exceptions to HTTP error responses."""

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return fn(*args, **kwargs)
        except tuple(_EXCEPTION_MAP) as exc:
            status_code, code = next(
                (sc, c)
                for cls, (sc, c) in _EXCEPTION_MAP.items()
                if isinstance(exc, cls)
            )
            logger.warning(
                "domain_error",
                extra={
                    "error_code": code,
                    "error_type": type(exc).__name__,
                },
            )
            return error_response(status_code, code, str(exc))
        except Exception:
            logger.exception("unhandled_error")
            return error_response(
                500,
                "internal_error",
                "Ocorreu um erro inesperado. Tente novamente.",
            )

    return wrapper
