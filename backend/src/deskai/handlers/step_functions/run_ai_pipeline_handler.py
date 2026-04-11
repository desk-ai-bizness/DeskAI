"""Lambda handler for AI pipeline execution (Step Functions trigger)."""

import logging
from typing import Any

from deskai.container import build_container
from deskai.domain.ai_pipeline.exceptions import PipelineError

logger = logging.getLogger(__name__)


def _extract_consultation_context(event: dict[str, Any]) -> tuple[str, str]:
    """Extract consultation context from direct or EventBridge-shaped payloads."""
    consultation_id = str(event.get("consultation_id", "") or "")
    clinic_id = str(event.get("clinic_id", "") or "")

    detail = event.get("detail")
    if isinstance(detail, dict):
        if not consultation_id:
            consultation_id = str(detail.get("consultation_id", "") or "")
        if not clinic_id:
            clinic_id = str(detail.get("clinic_id", "") or "")

    return consultation_id, clinic_id


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Execute the AI pipeline for a single consultation."""
    consultation_id, clinic_id = _extract_consultation_context(event)

    if not consultation_id or not clinic_id:
        logger.error(
            "pipeline_handler_invalid_event",
            extra={
                "consultation_id": consultation_id,
                "clinic_id": clinic_id,
            },
        )
        raise ValueError("Missing consultation_id or clinic_id")

    try:
        container = build_container()
        result = container.run_pipeline.execute(
            consultation_id=consultation_id, clinic_id=clinic_id
        )
        return {
            "consultation_id": result.consultation_id,
            "status": result.status.value,
            "artifacts_generated": len(result.completed_artifacts()),
            "error_message": result.error_message or None,
        }
    except PipelineError as exc:
        logger.error(
            "pipeline_handler_error",
            extra={
                "consultation_id": consultation_id,
                "error": str(exc),
            },
        )
        raise
    except Exception:
        logger.exception("pipeline_handler_unexpected_error")
        raise
