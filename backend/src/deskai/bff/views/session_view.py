"""BFF view builders for session responses."""

from deskai.domain.session.entities import Session


def build_session_start_view(
    session: Session,
    websocket_url: str,
    max_duration_minutes: int,
) -> dict:
    """Convert Session entity to the frontend-ready start view."""
    return {
        "session_id": session.session_id,
        "websocket_url": websocket_url,
        "connection_token": session.session_id,
        "max_duration_minutes": max_duration_minutes,
        "started_at": session.started_at,
    }


def build_session_end_view(session: Session) -> dict:
    """Convert Session entity to the frontend-ready end view."""
    return {
        "session_id": session.session_id,
        "ended_at": session.ended_at,
        "duration_seconds": session.duration_seconds,
        "status": "in_processing",
    }
