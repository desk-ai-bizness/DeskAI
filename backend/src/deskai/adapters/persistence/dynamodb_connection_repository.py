"""DynamoDB adapter for WebSocket connection persistence."""

import boto3

from deskai.domain.session.value_objects import ConnectionInfo
from deskai.ports.connection_repository import ConnectionRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBConnectionRepository(ConnectionRepository):
    """Persist and query WebSocket connections in DynamoDB.

    Key schema:
        PK = CONNECTION#{connection_id}
        SK = METADATA
    """

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def save(self, connection: ConnectionInfo) -> None:
        self._table.put_item(
            Item={
                "PK": f"CONNECTION#{connection.connection_id}",
                "SK": "METADATA",
                "connection_id": connection.connection_id,
                "session_id": connection.session_id,
                "doctor_id": connection.doctor_id,
                "clinic_id": connection.clinic_id,
                "connected_at": connection.connected_at,
            }
        )

    def find_by_connection_id(
        self, connection_id: str
    ) -> ConnectionInfo | None:
        response = self._table.get_item(
            Key={"PK": f"CONNECTION#{connection_id}", "SK": "METADATA"},
        )
        item = response.get("Item")
        if item is None:
            return None
        return self._to_entity(item)

    def remove(self, connection_id: str) -> None:
        self._table.delete_item(
            Key={"PK": f"CONNECTION#{connection_id}", "SK": "METADATA"},
        )

    @staticmethod
    def _to_entity(item: dict) -> ConnectionInfo:
        return ConnectionInfo(
            connection_id=item["connection_id"],
            session_id=item["session_id"],
            doctor_id=item["doctor_id"],
            clinic_id=item["clinic_id"],
            connected_at=item["connected_at"],
        )
