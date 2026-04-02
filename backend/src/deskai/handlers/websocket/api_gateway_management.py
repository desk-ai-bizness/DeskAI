"""Helper for sending messages back to connected WebSocket clients."""

import json

import boto3


class ApiGatewayManagement:
    """Send messages to connected WebSocket clients via API Gateway Management API."""

    def __init__(self, endpoint_url: str):
        self._client = boto3.client(
            "apigatewaymanagementapi", endpoint_url=endpoint_url
        )

    def send_to_connection(self, connection_id: str, data: dict) -> None:
        """Post a JSON payload to a connected WebSocket client."""
        self._client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode("utf-8"),
        )
