"""HTTP handler for POST /v1/consultations/{id}/transcription-token."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.handlers.http.middleware import (
    error_response,
    extract_auth_context,
    handle_domain_errors,
    json_response,
)

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_get_transcription_token(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """Issue a single-use transcription token for the consultation."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(
            400,
            "validation_error",
            "Consultation ID is required.",
        )

    token_data = container.issue_transcription_token.execute(
        consultation_id=consultation_id,
        doctor_id=auth.doctor_id,
        clinic_id=auth.clinic_id,
    )

    return json_response(200, token_data)
