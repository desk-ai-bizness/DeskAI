"""HTTP handler for consultation export."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.review_view import build_export_view
from deskai.handlers.http.middleware import (
    error_response,
    extract_auth_context,
    handle_domain_errors,
    json_response,
)

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_export(event: dict[str, Any], container: Container) -> dict[str, Any]:
    """POST /v1/consultations/{id}/export -- generate PDF export."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(400, "validation_error", "Consultation ID is required.")

    artifact = container.generate_export.execute(
        auth_context=auth,
        consultation_id=consultation_id,
        clinic_id=auth.clinic_id,
    )

    view = build_export_view(artifact)
    return json_response(200, view)
