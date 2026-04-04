"""DynamoDB adapter for WebSocket connection persistence."""

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.adapters.persistence.schema import ConnectionFields as F
from deskai.domain.session.value_objects import ConnectionInfo
from deskai.ports.connection_repository import ConnectionRepository
from deskai.shared.logging import get_logger, log_context

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
                F.PK: f"CONNECTION#{connection.connection_id}",
                F.SK: "METADATA",
                F.CONNECTION_ID: connection.connection_id,
                F.SESSION_ID: connection.session_id,
                F.DOCTOR_ID: connection.doctor_id,
                F.CLINIC_ID: connection.clinic_id,
                F.CONNECTED_AT: connection.connected_at,
            }
        )
        logger.info(
            "dynamodb_connection_saved",
            extra=log_context(
                connection_id=connection.connection_id, doctor_id=connection.doctor_id,
            ),
        )

    def find_by_connection_id(
        self, connection_id: str
    ) -> ConnectionInfo | None:
        response = self._safe_get_item(
            Key={F.PK: f"CONNECTION#{connection_id}", F.SK: "METADATA"},
        )
        item = response.get("Item")
        if item is None:
            logger.debug(
                "dynamodb_connection_not_found",
                extra=log_context(connection_id=connection_id),
            )
            return None
        logger.debug(
            "dynamodb_connection_found",
            extra=log_context(connection_id=connection_id),
        )
        return self._to_entity(item)

    def remove(self, connection_id: str) -> None:
        self._safe_delete_item(
            Key={F.PK: f"CONNECTION#{connection_id}", F.SK: "METADATA"},
        )
        logger.info("dynamodb_connection_removed", extra=log_context(connection_id=connection_id))

    @staticmethod
    def _to_entity(item: dict) -> ConnectionInfo:
        return ConnectionInfo(
            connection_id=item[F.CONNECTION_ID],
            session_id=item[F.SESSION_ID],
            doctor_id=item[F.DOCTOR_ID],
            clinic_id=item[F.CLINIC_ID],
            connected_at=item[F.CONNECTED_AT],
        )
