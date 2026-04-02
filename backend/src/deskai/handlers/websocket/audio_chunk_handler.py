"""WebSocket audio.chunk handler — forward audio data to transcription provider."""

import base64
import json

from deskai.domain.session.services import SessionService
from deskai.shared.time import utc_now_iso


def handle_audio_chunk(
    event: dict,
    connection_repo,
    session_repo,
    apigw,
    transcription_provider=None,
) -> dict:
    """Accept an audio chunk and forward it to the transcription provider."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        return {"statusCode": 400, "body": "Unknown connection"}

    session = session_repo.find_by_id(connection.session_id)
    if session is None:
        return {"statusCode": 400, "body": "Session not found"}

    try:
        SessionService.validate_audio_chunk(
            session_state=session.state,
            session_doctor_id=session.doctor_id,
            requesting_doctor_id=connection.doctor_id,
        )
    except Exception:
        return {"statusCode": 400, "body": "Audio chunk rejected"}

    audio_b64 = data.get("audio", "")
    if audio_b64 and transcription_provider is not None:
        audio_bytes = base64.b64decode(audio_b64)
        transcription_provider.send_audio_chunk(session.session_id, audio_bytes)

    session.audio_chunks_received += 1
    session.last_activity_at = utc_now_iso()
    session_repo.update(session)

    apigw.send_to_connection(
        connection_id=connection_id,
        data={
            "event": "transcript.partial",
            "data": {
                "text": "[stub transcript]",
                "speaker": "unknown",
                "is_final": False,
            },
        },
    )

    return {"statusCode": 200}
