"""HTTP handler for the current-user profile endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.bff.views.user_view import build_user_profile_view
from deskai.handlers.http.middleware import (
    handle_domain_errors,
    json_response,
)

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_get_me(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """GET /v1/me -- return the authenticated doctor profile and entitlements."""
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
    )
    cognito_sub = claims.get("sub", "")

    from deskai.domain.auth.exceptions import AuthenticationError

    if not cognito_sub:
        raise AuthenticationError("Missing user identity in request.")

    profile = container.get_current_user.execute(cognito_sub)
    entitlements = container.check_entitlements.execute(profile)

    view = build_user_profile_view(profile, entitlements)
    return json_response(200, view)
