"""BFF Lambda handler -- lightweight path/method router for HTTP API Gateway v2."""

from __future__ import annotations

import json
import os
import re
from typing import Any

_STAGE_PREFIX = f"/{os.environ.get('DESKAI_ENV', 'dev')}"

_container = None


def _get_container():
    """Lazy-initialize the container on first invocation (cold start)."""
    global _container
    if _container is None:
        from deskai.container import build_container

        _container = build_container()
    return _container


def handler(
    event: dict[str, Any], context: Any
) -> dict[str, Any]:
    """Route incoming HTTP API Gateway v2 events to the handler."""
    raw_path = event.get("rawPath", "/")
    path = raw_path.removeprefix(_STAGE_PREFIX) or "/"
    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", "GET")
        .upper()
    )

    if path == "/health" and method == "GET":
        return _health_response(context)

    container = _get_container()

    from deskai.handlers.http import (
        auth_handler,
        consultation_handler,
        me_handler,
        patient_handler,
    )

    # Exact-match routes
    _exact_routes: dict[tuple[str, str], Any] = {
        ("/v1/auth/session", "POST"): lambda: (
            auth_handler.handle_login(event, container)
        ),
        ("/v1/auth/session", "DELETE"): lambda: (
            auth_handler.handle_logout(event, container)
        ),
        ("/v1/auth/forgot-password", "POST"): lambda: (
            auth_handler.handle_forgot_password(event, container)
        ),
        (
            "/v1/auth/confirm-forgot-password",
            "POST",
        ): lambda: (
            auth_handler.handle_confirm_forgot_password(
                event, container
            )
        ),
        ("/v1/me", "GET"): lambda: (
            me_handler.handle_get_me(event, container)
        ),
        ("/v1/consultations", "POST"): lambda: (
            consultation_handler.handle_create_consultation(
                event, container
            )
        ),
        ("/v1/consultations", "GET"): lambda: (
            consultation_handler.handle_list_consultations(
                event, container
            )
        ),
        ("/v1/patients", "POST"): lambda: (
            patient_handler.handle_create_patient(
                event, container
            )
        ),
        ("/v1/patients", "GET"): lambda: (
            patient_handler.handle_list_patients(
                event, container
            )
        ),
    }

    # Parameterized routes: (compiled pattern, method, handler_fn)
    _param_routes = [
        (
            re.compile(r"^/v1/consultations/(?P<id>[^/]+)$"),
            "GET",
            consultation_handler.handle_get_consultation,
        ),
    ]

    # Try exact match first
    route_handler = _exact_routes.get((path, method))
    if route_handler is not None:
        return route_handler()

    # Try parameterized routes
    for pattern, route_method, handler_fn in _param_routes:
        if route_method == method:
            match = pattern.match(path)
            if match:
                event.setdefault("pathParameters", {})
                event["pathParameters"].update(match.groupdict())
                return handler_fn(event, container)

    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": {
                "code": "not_found",
                "message": "Recurso nao encontrado.",
            }
        }),
    }


def _health_response(context: Any) -> dict[str, Any]:
    """Return a minimal health check payload."""
    request_id = getattr(context, "aws_request_id", "unknown")
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "healthy",
            "request_id": request_id,
        }),
    }
