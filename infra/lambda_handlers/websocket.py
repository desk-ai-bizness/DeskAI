"""WebSocket Lambda entry point — delegates to backend router."""

from __future__ import annotations

from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Delegate to the backend WebSocket router."""
    from deskai.handlers.websocket.router import handler as ws_handler

    return ws_handler(event, context)
