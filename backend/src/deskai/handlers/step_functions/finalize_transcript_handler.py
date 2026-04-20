"""Lambda handler for transcript finalization (Step Functions step 1)."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _extract_context(event: dict[str, Any]) -> tuple[str, str, str]:
    """Extract session context from direct or EventBridge-shaped payloads."""
    session_id = str(event.get("session_id", "") or "")
    consultation_id = str(event.get("consultation_id", "") or "")
    clinic_id = str(event.get("clinic_id", "") or "")

    detail = event.get("detail")
    if isinstance(detail, dict):
        if not session_id:
            session_id = str(detail.get("session_id", "") or "")
        if not consultation_id:
            consultation_id = str(detail.get("consultation_id", "") or "")
        if not clinic_id:
            clinic_id = str(detail.get("clinic_id", "") or "")

    return session_id, consultation_id, clinic_id


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Finalize the transcript for a single consultation session."""
    session_id, consultation_id, clinic_id = _extract_context(event)

    if not session_id or not consultation_id or not clinic_id:
        logger.error(
            "finalize_transcript_handler_invalid_event",
            extra={
                "session_id": session_id,
                "consultation_id": consultation_id,
                "clinic_id": clinic_id,
            },
        )
        raise ValueError("Missing session_id, consultation_id, or clinic_id")

    from deskai.container import build_container

    container = build_container()
    result = container.finalize_transcript.execute(
        session_id=session_id,
        consultation_id=consultation_id,
        clinic_id=clinic_id,
    )

    return {
        "session_id": session_id,
        "consultation_id": consultation_id,
        "clinic_id": clinic_id,
        "status": "transcript_finalized",
        "completeness": str(result.completeness_status),
    }
