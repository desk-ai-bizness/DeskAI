"""Placeholder HTTP Lambda handler for the MVP BFF foundation."""

from __future__ import annotations

import json
from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Return a minimal health payload for foundation environments."""

    path = event.get("rawPath", "/")
    request_id = getattr(context, "aws_request_id", "unknown")

    body = {
        "message": "DeskAI BFF foundation endpoint",
        "path": path,
        "request_id": request_id,
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
