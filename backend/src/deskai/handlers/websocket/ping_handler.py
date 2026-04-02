"""WebSocket ping handler — keepalive response."""

from deskai.shared.time import utc_now_iso


def handle_ping(event: dict) -> dict:
    """Respond to client.ping with server.pong."""
    return {
        "statusCode": 200,
        "body": {
            "event": "server.pong",
            "data": {"timestamp": utc_now_iso()},
        },
    }
