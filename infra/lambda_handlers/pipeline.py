"""Placeholder processing handler invoked by the Step Functions foundation flow."""

from __future__ import annotations

from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Return deterministic metadata without persisting sensitive payloads."""

    request_id = getattr(context, "aws_request_id", "unknown")
    consultation_id = event.get("consultation_id", "unknown")
    return {
        "request_id": request_id,
        "consultation_id": consultation_id,
        "status": "processing-placeholder-complete",
    }
