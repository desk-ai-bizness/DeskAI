"""Pipeline Lambda entry point — delegates to backend handler."""

from __future__ import annotations

from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Delegate to the backend AI pipeline handler."""
    from deskai.handlers.step_functions.run_ai_pipeline_handler import (
        handler as pipeline_handler,
    )

    return pipeline_handler(event, context)
