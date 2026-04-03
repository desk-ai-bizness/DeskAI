"""HTTP handler for the UI configuration endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.domain.auth.exceptions import AuthenticationError
from deskai.domain.auth.value_objects import AuthContext
from deskai.handlers.http.middleware import (
    handle_domain_errors,
    json_response,
)

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_get_ui_config(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """GET /v1/ui-config -- return backend-driven UI configuration."""
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    cognito_sub = claims.get("sub", "")

    if not cognito_sub:
        raise AuthenticationError(
            "Missing user identity in request."
        )

    profile = container.get_current_user.execute(cognito_sub)
    auth_context = AuthContext(
        doctor_id=profile.doctor_id,
        email=claims.get("email", profile.email),
        clinic_id=profile.clinic_id,
        plan_type=profile.plan_type,
    )

    config = container.get_ui_config.execute(auth_context)
    return json_response(200, config)
