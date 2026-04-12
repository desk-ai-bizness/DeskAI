"""WebSocket session.stop handler — end session and trigger finalization."""

import json

from deskai.shared.logging import get_logger, log_context

logger = get_logger()


def handle_session_stop(
    event: dict,
    connection_repo,
    end_session_use_case,
    apigw,
    transcription_provider=None,
    finalize_transcript_use_case=None,
) -> dict:
    """End a session via WebSocket and optionally trigger finalization."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})
    consultation_id = data.get("consultation_id", "")

    logger.info(
        "ws_session_stop_requested",
        extra=log_context(connection_id=connection_id, consultation_id=consultation_id),
    )

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is not None:
        doctor_id = connection.doctor_id
        clinic_id = connection.clinic_id
    else:
        # Connection may have been removed by $disconnect racing ahead.
        # Fall back to the authorizer context propagated by API Gateway.
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        doctor_id = authorizer.get("doctor_id", "")
        clinic_id = authorizer.get("clinic_id", "")
        if not doctor_id or not clinic_id:
            logger.warning(
                "ws_session_stop_no_connection_or_context",
                extra=log_context(connection_id=connection_id),
            )
            return {"statusCode": 400, "body": "Unknown connection"}
        logger.info(
            "ws_session_stop_using_authorizer_context",
            extra=log_context(connection_id=connection_id, doctor_id=doctor_id),
        )

    session = end_session_use_case.execute(
        consultation_id=consultation_id,
        doctor_id=doctor_id,
        clinic_id=clinic_id,
    )

    if transcription_provider is not None:
        try:
            transcription_provider.finish_realtime_session(session.session_id)
        except Exception:
            logger.exception(
                "ws_session_stop_provider_finish_failed",
                extra=log_context(
                    session_id=session.session_id,
                    consultation_id=consultation_id,
                ),
            )

    try:
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
    except Exception:
        logger.info(
            "ws_session_stop_send_skipped",
            extra=log_context(
                connection_id=connection_id,
                reason="connection_gone",
            ),
        )

    if finalize_transcript_use_case is not None:
        try:
            finalize_transcript_use_case.execute(
                session_id=session.session_id,
                consultation_id=consultation_id,
                clinic_id=clinic_id,
            )
        except Exception:
            logger.exception(
                "ws_session_stop_finalization_failed",
                extra=log_context(
                    session_id=session.session_id,
                    consultation_id=consultation_id,
                ),
            )

    logger.info(
        "ws_session_stop_completed",
        extra=log_context(session_id=session.session_id, consultation_id=consultation_id),
    )
    return {"statusCode": 200}
