"""HTTP handlers for review endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.review_view import build_review_view
from deskai.domain.review.value_objects import ReviewUpdate
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
def handle_get_review(event: dict[str, Any], container: Container) -> dict[str, Any]:
    """GET /v1/consultations/{id}/review -- open review screen."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(400, "validation_error", "Consultation ID is required.")

    payload = container.open_review.execute(
        auth_context=auth,
        consultation_id=consultation_id,
        clinic_id=auth.clinic_id,
    )

    view = build_review_view(payload)
    return json_response(200, view)


@handle_domain_errors
def handle_update_review(event: dict[str, Any], container: Container) -> dict[str, Any]:
    """PUT /v1/consultations/{id}/review -- apply physician edits."""
    auth = extract_auth_context(event, container.get_current_user)
    path_params = event.get("pathParameters") or {}
    consultation_id = path_params.get("id")

    if not consultation_id:
        return error_response(400, "validation_error", "Consultation ID is required.")

    body = parse_json_body(event)
    update = ReviewUpdate(
        medical_history=body.get("medical_history"),
        summary=body.get("summary"),
        insight_actions=body.get("insights"),
    )

    container.update_review.execute(
        auth_context=auth,
        consultation_id=consultation_id,
        clinic_id=auth.clinic_id,
        update=update,
    )

    # Re-load the review payload to return the updated state
    payload = container.open_review.execute(
        auth_context=auth,
        consultation_id=consultation_id,
        clinic_id=auth.clinic_id,
    )

    view = build_review_view(payload)
    return json_response(200, view)
