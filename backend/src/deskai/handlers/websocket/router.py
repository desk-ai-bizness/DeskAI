"""WebSocket Lambda router — routes API Gateway WebSocket events to handlers."""

import json

from deskai.shared.logging import get_logger, log_context

logger = get_logger()

_container = None


def _get_container():
    """Lazy-initialize the container on first invocation (cold start)."""
    global _container
    if _container is None:
        from deskai.container import build_container

        _container = build_container()
    return _container


def _build_apigw(event: dict):
    """Build ApiGatewayManagement from the WebSocket event context."""
    from deskai.handlers.websocket.api_gateway_management import (
        ApiGatewayManagement,
    )

    rc = event.get("requestContext", {})
    domain = rc.get("domainName", "")
    stage = rc.get("stage", "")
    endpoint_url = f"https://{domain}/{stage}"
    return ApiGatewayManagement(endpoint_url=endpoint_url)


def _handle_authorizer(event: dict) -> dict:
    """Handle WebSocket Lambda authorizer REQUEST-type events.

    API Gateway calls this Lambda both as authorizer (``type=REQUEST``)
    and as the regular route handler.  For the authorizer call we build
    the container lazily (same cold-start as ``$connect``) and delegate
    token validation to the auth provider.
    """
    token = (event.get("queryStringParameters") or {}).get("token", "")
    method_arn = event.get("methodArn", "")

    if not token:
        logger.warning("ws_authorizer_no_token")
        return _deny_policy(method_arn)

    try:
        c = _get_container()
        claims = c.auth_provider.validate_ws_token(token)
        return {
            "principalId": claims.get("sub", "unknown"),
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Allow",
                        "Resource": method_arn,
                    }
                ],
            },
            "context": {
                "sub": claims.get("sub", ""),
                "doctor_id": claims.get("doctor_id", ""),
                "clinic_id": claims.get("clinic_id", ""),
            },
        }
    except Exception:
        logger.warning("ws_authorizer_denied")
        return _deny_policy(method_arn)


def _deny_policy(method_arn: str) -> dict:
    return {
        "principalId": "unauthorized",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": method_arn,
                }
            ],
        },
    }


def handler(event: dict, context) -> dict:
    """Route WebSocket events to the appropriate handler."""
    # Detect authorizer invocation (no routeKey, has type=REQUEST).
    if event.get("type") == "REQUEST":
        return _handle_authorizer(event)

    route_key = event.get("requestContext", {}).get("routeKey", "")

    connection_id = event.get("requestContext", {}).get("connectionId", "")

    if route_key == "$connect":
        from deskai.handlers.websocket.connect_handler import handle_connect

        logger.info("ws_connect", extra=log_context(connection_id=connection_id))
        c = _get_container()
        return handle_connect(event, c.connection_repo, c.auth_provider)

    if route_key == "$disconnect":
        from deskai.handlers.websocket.disconnect_handler import handle_disconnect

        logger.info("ws_disconnect", extra=log_context(connection_id=connection_id))
        c = _get_container()
        return handle_disconnect(event, c.connection_repo, c.session_repo)

    # Named routes arrive with their route key directly (e.g. "session.init").
    # $default carries the action in the body.  Normalise both to ``action``.
    if route_key == "$default":
        body = json.loads(event.get("body", "{}"))
        action = body.get("action", "")
    else:
        action = route_key

    if action:
        logger.debug(
            "ws_route", extra=log_context(action=action, connection_id=connection_id),
        )
        if action == "session.init":
            from deskai.handlers.websocket.session_init_handler import (
                handle_session_init,
            )

            c = _get_container()
            return handle_session_init(
                event,
                c.connection_repo,
                c.session_repo,
                _build_apigw(event),
                c.transcription_provider,
            )

        if action == "audio.chunk":
            from deskai.handlers.websocket.audio_chunk_handler import (
                handle_audio_chunk,
            )

            c = _get_container()
            return handle_audio_chunk(
                event,
                c.connection_repo,
                c.session_repo,
                _build_apigw(event),
                c.transcription_provider,
            )

        if action == "session.stop":
            from deskai.handlers.websocket.session_stop_handler import (
                handle_session_stop,
            )

            c = _get_container()
            return handle_session_stop(
                event,
                c.connection_repo,
                c.end_session,
                _build_apigw(event),
                c.transcription_provider,
                c.finalize_transcript,
            )

        if action == "client.ping":
            from deskai.handlers.websocket.ping_handler import handle_ping

            return handle_ping(event)

    logger.warning("ws_unrecognized_route", extra=log_context(route_key=route_key))
    return {"statusCode": 400, "body": "Unrecognized route"}
