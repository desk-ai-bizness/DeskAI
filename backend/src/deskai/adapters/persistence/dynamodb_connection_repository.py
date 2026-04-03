"""DynamoDB adapter for WebSocket connection persistence."""

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.domain.session.value_objects import ConnectionInfo
from deskai.ports.connection_repository import ConnectionRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBConnectionRepository(DynamoDBBaseRepository, ConnectionRepository):
    """Persist and query WebSocket connections in DynamoDB.

    Key schema:
        PK = CONNECTION#{connection_id}
        SK = METADATA
    """

    def save(self, connection: ConnectionInfo) -> None:
        self._safe_put_item(
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
        response = self._safe_get_item(
            Key={"PK": f"CONNECTION#{connection_id}", "SK": "METADATA"},
        )
        item = response.get("Item")
        if item is None:
            return None
        return self._to_entity(item)

    def remove(self, connection_id: str) -> None:
        self._safe_delete_item(
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
