"""Helper for sending messages back to connected WebSocket clients."""

import json

import boto3
from botocore.exceptions import ClientError

from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class ApiGatewayManagement:
    """Send messages to connected WebSocket clients via API Gateway Management API."""

    def __init__(self, endpoint_url: str):
        self._client = boto3.client(
            "apigatewaymanagementapi", endpoint_url=endpoint_url
        )

    def send_to_connection(self, connection_id: str, data: dict) -> None:
        """Post a JSON payload to a connected WebSocket client."""
        event_type = data.get("event", "")
        try:
            self._client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(data).encode("utf-8"),
            )
            logger.debug(
                "ws_message_sent",
                extra=log_context(connection_id=connection_id, event=event_type),
            )
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "GoneException":
                logger.warning(
                    "ws_connection_gone",
                    extra=log_context(connection_id=connection_id, event=event_type),
                )
            else:
                logger.error(
                    "ws_send_failed",
                    extra=log_context(
                        connection_id=connection_id, event=event_type, error_code=error_code,
                    ),
                )
            raise
