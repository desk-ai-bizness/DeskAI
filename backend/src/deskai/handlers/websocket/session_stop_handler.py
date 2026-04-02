"""WebSocket session.stop handler — end session and trigger finalization."""

import json
import logging

logger = logging.getLogger(__name__)


def handle_session_stop(
    event: dict,
    connection_repo,
    end_session_use_case,
    apigw,
    finalize_transcript_use_case=None,
) -> dict:
    """End a session via WebSocket and optionally trigger finalization."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})
    consultation_id = data.get("consultation_id", "")

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        return {"statusCode": 400, "body": "Unknown connection"}

    session = end_session_use_case.execute(
        consultation_id=consultation_id,
        doctor_id=connection.doctor_id,
        clinic_id=connection.clinic_id,
    )

    apigw.send_to_connection(
        connection_id=connection_id,
        data={
            "event": "session.ended",
            "data": {
                "reason": "manual",
                "message": "Sessao encerrada.",
            },
        },
    )

    if finalize_transcript_use_case is not None:
        try:
            finalize_transcript_use_case.execute(
                session_id=session.session_id,
                consultation_id=consultation_id,
                clinic_id=connection.clinic_id,
            )
        except Exception:
            logger.exception(
                "Finalization failed for session %s", session.session_id
            )

    return {"statusCode": 200}
