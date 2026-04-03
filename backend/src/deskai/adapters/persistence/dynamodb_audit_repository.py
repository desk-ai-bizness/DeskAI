"""DynamoDB adapter for audit trail persistence."""

import json

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.ports.audit_repository import AuditRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBAuditRepository(DynamoDBBaseRepository, AuditRepository):
    """Append-only audit trail in DynamoDB.

    Key schema:
        PK = CONSULTATION#{consultation_id}
        SK = AUDIT#{timestamp}#{event_id}
    """

    def append(self, event: AuditEvent) -> None:
        item: dict[str, object] = {
            "PK": f"CONSULTATION#{event.consultation_id}",
            "SK": f"AUDIT#{event.timestamp}#{event.event_id}",
            "event_id": event.event_id,
            "consultation_id": event.consultation_id,
            "event_type": str(event.event_type),
            "actor_id": event.actor_id,
            "timestamp": event.timestamp,
        }
        if event.payload is not None:
            item["payload"] = json.dumps(event.payload)

        self._safe_put_item(Item=item)

    def find_by_consultation(
        self, consultation_id: str
    ) -> list[AuditEvent]:
        items = self._paginated_query(
            KeyConditionExpression=(
                "PK = :pk AND begins_with(SK, :sk_prefix)"
            ),
            ExpressionAttributeValues={
                ":pk": f"CONSULTATION#{consultation_id}",
                ":sk_prefix": "AUDIT#",
            },
        )
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(item: dict) -> AuditEvent:
        raw_payload = item.get("payload")
        payload = json.loads(raw_payload) if raw_payload else None

        return AuditEvent(
            event_id=item["event_id"],
            consultation_id=item["consultation_id"],
            event_type=AuditAction(item["event_type"]),
            actor_id=item["actor_id"],
            timestamp=item["timestamp"],
            payload=payload,
        )
