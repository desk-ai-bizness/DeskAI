"""WebSocket $connect handler — validate auth token and store connection."""

from deskai.domain.session.value_objects import ConnectionInfo
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


def handle_connect(event: dict, connection_repo, auth_provider) -> dict:
    """Accept or reject a WebSocket connection based on token validation."""
    connection_id = event["requestContext"]["connectionId"]

    query_params = event.get("queryStringParameters") or {}
    token = query_params.get("token")
    if not token:
        logger.warning("ws_connect_no_token", extra=log_context(connection_id=connection_id))
        return {"statusCode": 401}

    try:
        claims = auth_provider.validate_ws_token(token)
    except Exception:
        logger.warning("ws_connect_auth_failed", extra=log_context(connection_id=connection_id))
        return {"statusCode": 401}

    connection = ConnectionInfo(
        connection_id=connection_id,
        session_id="",
        doctor_id=claims["doctor_id"],
        clinic_id=claims["clinic_id"],
        connected_at=utc_now_iso(),
    )
    connection_repo.save(connection)
    logger.info(
        "ws_connection_accepted",
        extra=log_context(connection_id=connection_id, doctor_id=claims["doctor_id"]),
    )

    return {"statusCode": 200}
