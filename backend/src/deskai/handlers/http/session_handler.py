"""HTTP handlers for session endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.session_view import (
    build_session_end_view,
    build_session_start_view,
)
from deskai.handlers.http.middleware import (
    error_response,
    extract_auth_context,
    handle_domain_errors,
    json_response,
)

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_start_session(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """POST /v1/consultations/{id}/session/start."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(
            400,
            "validation_error",
            "Consultation ID is required.",
        )

    session = container.start_session.execute(
        consultation_id=consultation_id,
        doctor_id=auth.doctor_id,
        clinic_id=auth.clinic_id,
    )
    view = build_session_start_view(
        session,
        websocket_url=container.settings.websocket_url,
        max_duration_minutes=container.settings.max_session_duration_minutes,
    )
    return json_response(200, view)


@handle_domain_errors
def handle_end_session(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """POST /v1/consultations/{id}/session/end."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(
            400,
            "validation_error",
            "Consultation ID is required.",
        )

    session = container.end_session.execute(
        consultation_id=consultation_id,
        doctor_id=auth.doctor_id,
        clinic_id=auth.clinic_id,
    )
    view = build_session_end_view(session)
    return json_response(200, view)
