"""WebSocket session.init handler — bind connection to a consultation session."""

import json
from dataclasses import replace

from deskai.domain.session.entities import SessionState
from deskai.shared.time import utc_now_iso


def handle_session_init(event: dict, connection_repo, session_repo, apigw) -> dict:
    """Bind a WebSocket connection to a consultation session."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})
    session_id = data.get("session_id", "")
    _consultation_id = data.get("consultation_id", "")  # noqa: F841

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        return {"statusCode": 400, "body": "Unknown connection"}

    session = session_repo.find_by_id(session_id)
    if session is None:
        return {"statusCode": 400, "body": "Session not found"}

    if session.doctor_id != connection.doctor_id:
        return {"statusCode": 403, "body": "Session ownership mismatch"}

    session = replace(
        session,
        connection_id=connection_id,
        state=SessionState.RECORDING,
        last_activity_at=utc_now_iso(),
    )
    session_repo.update(session)

    apigw.send_to_connection(
        connection_id=connection_id,
        data={
            "event": "session.status",
            "data": {
                "status": "recording",
                "session_id": session_id,
                "message": "Sessao iniciada com sucesso.",
            },
        },
    )

    return {"statusCode": 200}
