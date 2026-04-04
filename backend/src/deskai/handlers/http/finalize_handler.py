"""HTTP handler for consultation finalization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.review_view import build_finalize_view
from deskai.handlers.http.middleware import (
    error_response,
    extract_auth_context,
    handle_domain_errors,
    json_response,
)

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_finalize(event: dict[str, Any], container: Container) -> dict[str, Any]:
    """POST /v1/consultations/{id}/finalize -- physician confirms final record."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(400, "validation_error", "Consultation ID is required.")

    consultation = container.finalize_consultation.execute(
        auth_context=auth,
        consultation_id=consultation_id,
        clinic_id=auth.clinic_id,
    )

    view = build_finalize_view(consultation)
    return json_response(200, view)
