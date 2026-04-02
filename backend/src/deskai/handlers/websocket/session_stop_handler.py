"""WebSocket session.stop handler — end session via WebSocket."""

import json


def handle_session_stop(event: dict, connection_repo, end_session_use_case, apigw) -> dict:
    """End a session via WebSocket, same effect as POST .../session/end."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})
    consultation_id = data.get("consultation_id", "")

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        return {"statusCode": 400, "body": "Unknown connection"}

    end_session_use_case.execute(
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

    return {"statusCode": 200}
