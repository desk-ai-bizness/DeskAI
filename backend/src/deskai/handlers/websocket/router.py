"""WebSocket Lambda router — routes API Gateway WebSocket events to handlers."""

import json
import logging

logger = logging.getLogger(__name__)

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


def handler(event: dict, context) -> dict:
    """Route WebSocket events to the appropriate handler."""
    route_key = event.get("requestContext", {}).get("routeKey", "")

    if route_key == "$connect":
        from deskai.handlers.websocket.connect_handler import handle_connect

        c = _get_container()
        return handle_connect(event, c.connection_repo, c.auth_provider)

    if route_key == "$disconnect":
        from deskai.handlers.websocket.disconnect_handler import handle_disconnect

        c = _get_container()
        return handle_disconnect(event, c.connection_repo, c.session_repo)

    if route_key == "$default":
        body = json.loads(event.get("body", "{}"))
        action = body.get("action", "")

        if action == "session.init":
            from deskai.handlers.websocket.session_init_handler import (
                handle_session_init,
            )

            c = _get_container()
            return handle_session_init(
                event, c.connection_repo, c.session_repo, _build_apigw(event)
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
                c.finalize_transcript,
            )

        if action == "client.ping":
            from deskai.handlers.websocket.ping_handler import handle_ping

            return handle_ping(event)

    logger.warning("Unrecognized route: %s", route_key)
    return {"statusCode": 400, "body": "Unrecognized route"}
