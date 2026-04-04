"""HTTP handlers for authentication endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from deskai.handlers.http.middleware import (
    error_response,
    handle_domain_errors,
    json_response,
    no_content_response,
    parse_json_body,
)
from deskai.shared.logging import get_logger

logger = get_logger()

if TYPE_CHECKING:
    from deskai.container import Container


@handle_domain_errors
def handle_login(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """POST /v1/auth/session -- authenticate with email and password."""
    body = parse_json_body(event)
    email = body.get("email", "")
    password = body.get("password", "")

    if not email or not password:
        return error_response(
            400,
            "validation_error",
            "Email e senha sao obrigatorios.",
        )

    tokens = container.authenticate.execute(email, password)
    logger.info("auth_login_success")
    return json_response(200, {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "expires_in": tokens.expires_in,
    })


@handle_domain_errors
def handle_logout(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """DELETE /v1/auth/session -- sign out the current user."""
    auth_header = (
        event.get("headers", {}).get("authorization", "")
    )
    token = auth_header.removeprefix("Bearer ").strip()

    if not token:
        return error_response(
            401, "unauthorized", "Token nao fornecido."
        )

    container.sign_out.execute(token)
    logger.info("auth_logout_success")
    return no_content_response()


@handle_domain_errors
def handle_forgot_password(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """POST /v1/auth/forgot-password -- initiate password reset."""
    body = parse_json_body(event)
    email = body.get("email", "")

    if not email:
        return error_response(
            400,
            "validation_error",
            "Email e obrigatorio.",
        )

    container.forgot_password.execute(email)
    logger.info("auth_forgot_password_requested")
    return json_response(200, {
        "message": (
            "Se o email estiver cadastrado, voce recebera"
            " um codigo de verificacao."
        ),
    })


@handle_domain_errors
def handle_confirm_forgot_password(
    event: dict[str, Any], container: Container
) -> dict[str, Any]:
    """POST /v1/auth/confirm-forgot-password -- complete password reset."""
    body = parse_json_body(event)
    email = body.get("email", "")
    code = body.get("confirmation_code", "")
    new_password = body.get("new_password", "")

    if not email or not code or not new_password:
        return error_response(
            400,
            "validation_error",
            "Email, codigo de confirmacao e nova senha"
            " sao obrigatorios.",
        )

    container.confirm_forgot_password.execute(
        email, code, new_password
    )
    logger.info("auth_password_reset_confirmed")
    return json_response(
        200, {"message": "Senha alterada com sucesso."}
    )
