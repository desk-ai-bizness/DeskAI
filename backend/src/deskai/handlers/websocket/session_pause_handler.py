"""WebSocket session.pause handler — pause an active recording session."""

import json

from deskai.shared.logging import get_logger, log_context

logger = get_logger()


def handle_session_pause(
    event: dict,
    connection_repo,
    pause_use_case,
    apigw,
) -> dict:
    """Validate connection, delegate to PauseSessionUseCase, notify client."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})
    consultation_id = data.get("consultation_id", "")

    logger.info(
        "ws_session_pause_requested",
        extra=log_context(
            connection_id=connection_id,
            consultation_id=consultation_id,
        ),
    )

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        logger.warning(
            "ws_session_pause_unknown_connection",
            extra=log_context(connection_id=connection_id),
        )
        return {"statusCode": 400, "body": "Unknown connection"}

    session = pause_use_case.execute(
        consultation_id=consultation_id,
        doctor_id=connection.doctor_id,
    )

    apigw.send_to_connection(
        connection_id=connection_id,
        data={
            "event": "session.status",
            "event_version": "2",
            "data": {
                "status": "paused",
                "session_id": session.session_id,
                "message": "Sessao pausada.",
            },
        },
    )

    logger.info(
        "ws_session_pause_completed",
        extra=log_context(
            session_id=session.session_id,
            consultation_id=consultation_id,
        ),
    )
    return {"statusCode": 200}
