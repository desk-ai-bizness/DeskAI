"""WebSocket Lambda router — routes API Gateway WebSocket events to handlers."""

import json
import logging

logger = logging.getLogger(__name__)


def handler(event: dict, context) -> dict:
    """Route WebSocket events to the appropriate handler."""
    route_key = event.get("requestContext", {}).get("routeKey", "")

    if route_key == "$connect":
        from deskai.handlers.websocket.connect_handler import handle_connect

        return handle_connect(event, _get_connection_repo(), _get_auth_provider())

    if route_key == "$disconnect":
        from deskai.handlers.websocket.disconnect_handler import handle_disconnect

        return handle_disconnect(event, _get_connection_repo(), _get_session_repo())

    if route_key == "$default":
        body = json.loads(event.get("body", "{}"))
        action = body.get("action", "")

        if action == "session.init":
            from deskai.handlers.websocket.session_init_handler import (
                handle_session_init,
            )

            return handle_session_init(
                event, _get_connection_repo(), _get_session_repo(), _get_apigw()
            )

        if action == "audio.chunk":
            from deskai.handlers.websocket.audio_chunk_handler import (
                handle_audio_chunk,
            )

            return handle_audio_chunk(
                event, _get_connection_repo(), _get_session_repo(), _get_apigw()
            )

        if action == "session.stop":
            from deskai.handlers.websocket.session_stop_handler import (
                handle_session_stop,
            )

            return handle_session_stop(
                event,
                _get_connection_repo(),
                _get_end_session_use_case(),
                _get_apigw(),
            )

        if action == "client.ping":
            from deskai.handlers.websocket.ping_handler import handle_ping

            return handle_ping(event)

    logger.warning("Unrecognized route: %s", route_key)
    return {"statusCode": 400, "body": "Unrecognized route"}


# ---------------------------------------------------------------------------
# Dependency stubs — will be fully wired when container supports WebSocket
# ---------------------------------------------------------------------------


def _get_connection_repo():
    raise NotImplementedError("Wire WebSocket container")


def _get_session_repo():
    raise NotImplementedError("Wire WebSocket container")


def _get_auth_provider():
    raise NotImplementedError("Wire WebSocket container")


def _get_apigw():
    raise NotImplementedError("Wire WebSocket container")


def _get_end_session_use_case():
    raise NotImplementedError("Wire WebSocket container")
