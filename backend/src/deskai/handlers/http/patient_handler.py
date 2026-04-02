"""HTTP handlers for patient endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.consultation_view import build_patient_view
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
def handle_create_patient(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """POST /v1/patients -- create a new patient in the clinic."""
    auth = extract_auth_context(event, container.get_current_user)
    body = parse_json_body(event)

    name = body.get("name")
    dob = body.get("date_of_birth")

    if not name or not dob:
        return error_response(
            400,
            "validation_error",
            "name and date_of_birth are required.",
        )

    patient = container.create_patient.execute(auth, name, dob)
    view = build_patient_view(patient)
    return json_response(201, view)


@handle_domain_errors
def handle_list_patients(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """GET /v1/patients -- list patients in the clinic."""
    auth = extract_auth_context(event, container.get_current_user)
    params = event.get("queryStringParameters") or {}

    patients = container.list_patients.execute(
        auth.clinic_id, params.get("search", "")
    )
    return json_response(
        200, {"patients": [build_patient_view(p) for p in patients]}
    )
