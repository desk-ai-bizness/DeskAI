"""WebSocket transcript.commit handler — persist committed transcript segments."""

import json

from deskai.domain.session.entities import SessionState
from deskai.domain.transcription.value_objects import CommittedSegment
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


def handle_transcript_commit(
    event: dict,
    connection_repo,
    session_repo,
    segment_repo,
    apigw,
) -> dict:
    """Validate connection and session, then persist committed segments."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})
    consultation_id = data.get("consultation_id", "")

    logger.info(
        "ws_transcript_commit_requested",
        extra=log_context(
            connection_id=connection_id,
            consultation_id=consultation_id,
        ),
    )

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        logger.warning(
            "ws_transcript_commit_unknown_connection",
            extra=log_context(connection_id=connection_id),
        )
        return {"statusCode": 400, "body": "Unknown connection"}

    session = session_repo.find_by_id(connection.session_id)
    if session is None or session.state != SessionState.RECORDING:
        logger.warning(
            "ws_transcript_commit_rejected",
            extra=log_context(
                connection_id=connection_id,
                consultation_id=consultation_id,
                reason="not_recording",
            ),
        )
        return {"statusCode": 400, "body": "Session not recording"}

    raw_segments = data.get("segments", [])
    now = utc_now_iso()

    committed = [
        CommittedSegment(
            consultation_id=consultation_id,
            session_id=session.session_id,
            speaker=seg["speaker"],
            text=seg["text"],
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            confidence=seg["confidence"],
            is_final=seg.get("is_final", False),
            received_at=now,
            segment_index=idx,
        )
        for idx, seg in enumerate(raw_segments)
    ]

    segment_repo.save_batch(committed)

    logger.info(
        "ws_transcript_commit_accepted",
        extra=log_context(
            consultation_id=consultation_id,
            segment_count=len(committed),
        ),
    )
    return {"statusCode": 200}
