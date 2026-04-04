"""HTTP handlers for consultation endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.consultation_view import (
    build_consultation_detail_view,
    build_consultation_list_view,
    build_consultation_view,
)
from deskai.handlers.http.middleware import (
    error_response,
    extract_auth_context,
    handle_domain_errors,
    json_response,
    parse_json_body,
)

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_create_consultation(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """POST /v1/consultations -- create a new consultation."""
    auth = extract_auth_context(event, container.get_current_user)
    body = parse_json_body(event)

    patient_id = body.get("patient_id")
    scheduled_date = body.get("scheduled_date")

    if not patient_id or not scheduled_date:
        return error_response(
            400,
            "validation_error",
            "patient_id and scheduled_date are required.",
        )

    consultation = container.create_consultation.execute(
        auth_context=auth,
        patient_id=patient_id,
        specialty=body.get("specialty", "general_practice"),
        scheduled_date=scheduled_date,
        notes=body.get("notes", ""),
    )
    view = build_consultation_view(consultation)
    return json_response(201, view)


@handle_domain_errors
def handle_list_consultations(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """GET /v1/consultations -- list consultations for the authenticated doctor."""
    auth = extract_auth_context(event, container.get_current_user)
    params = event.get("queryStringParameters") or {}

    consultations = container.list_consultations.execute(
        doctor_id=auth.doctor_id,
        start_date=params.get("from", ""),
        end_date=params.get("to", ""),
    )

    status_filter = params.get("status")
    if status_filter:
        consultations = [c for c in consultations if c.status.value == status_filter]

    page = int(params.get("page", 1))
    page_size = int(params.get("page_size", 20))

    view = build_consultation_list_view(consultations, page=page, page_size=page_size)
    return json_response(200, view)


@handle_domain_errors
def handle_get_consultation(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """GET /v1/consultations/{id} -- get a single consultation."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(
            400,
            "validation_error",
            "Consultation ID is required.",
        )

    consultation = container.get_consultation.execute(
        auth_context=auth,
        consultation_id=consultation_id,
        clinic_id=auth.clinic_id,
    )

    view = build_consultation_detail_view(consultation)
    return json_response(200, view)
