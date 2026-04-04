"""Lambda handler for AI pipeline execution (Step Functions trigger)."""

import logging
from typing import Any

from deskai.container import build_container
from deskai.domain.ai_pipeline.exceptions import PipelineError

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Execute the AI pipeline for a single consultation."""
    consultation_id = event.get("consultation_id", "")
    clinic_id = event.get("clinic_id", "")

    if not consultation_id or not clinic_id:
        return {
            "status": "error",
            "error": "Missing consultation_id or clinic_id",
        }

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
        return {
            "consultation_id": consultation_id,
            "status": "error",
            "error": str(exc),
        }
    except Exception:
        logger.exception("pipeline_handler_unexpected_error")
        return {
            "consultation_id": consultation_id,
            "status": "error",
            "error": "Internal error",
        }
