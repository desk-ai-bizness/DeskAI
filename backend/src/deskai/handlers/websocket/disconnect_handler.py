"""WebSocket $disconnect handler — start grace period for active sessions."""

from deskai.domain.session.entities import SessionState
from deskai.domain.session.services import SessionService
from deskai.shared.time import utc_now_iso


def handle_disconnect(event: dict, connection_repo, session_repo) -> dict:
    """Handle WebSocket disconnection — set grace period if session is active."""
    connection_id = event["requestContext"]["connectionId"]

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        return {"statusCode": 200}

    if connection.session_id:
        session = session_repo.find_by_id(connection.session_id)
        if session and session.state in (SessionState.RECORDING, SessionState.ACTIVE):
            now = utc_now_iso()
            session.state = SessionState.DISCONNECTED
            session.grace_period_expires_at = SessionService.compute_grace_period_expiry(now)
            session_repo.update(session)

    connection_repo.remove(connection_id)

    return {"statusCode": 200}
