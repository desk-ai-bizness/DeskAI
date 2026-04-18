"""HTTP handlers for patient endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.consultation_view import build_patient_detail_view, build_patient_view
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
    cpf = body.get("cpf")
    dob = body.get("date_of_birth")

    if not name or not cpf:
        return error_response(
            400,
            "validation_error",
            "name and cpf are required.",
        )

    patient = container.create_patient.execute(
        auth_context=auth,
        name=name,
        cpf=cpf,
        date_of_birth=dob,
    )
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


@handle_domain_errors
def handle_get_patient(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """GET /v1/patients/{patient_id} -- load patient detail and safe history."""
    auth = extract_auth_context(event, container.get_current_user)
    patient_id = (event.get("pathParameters") or {}).get("id")
    if not patient_id:
        return error_response(400, "validation_error", "patient_id is required.")

    result = container.get_patient_detail.execute(auth, patient_id)
    return json_response(200, build_patient_detail_view(result))
