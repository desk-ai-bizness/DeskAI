"""Placeholder export handler for MVP infrastructure foundation."""

from __future__ import annotations

from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Return baseline export metadata without generating documents yet."""

    request_id = getattr(context, "aws_request_id", "unknown")
    consultation_id = event.get("consultation_id", "unknown")
    return {
        "request_id": request_id,
        "consultation_id": consultation_id,
        "status": "export-placeholder-ready",
    }
