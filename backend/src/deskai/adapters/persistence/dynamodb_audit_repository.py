"""DynamoDB adapter for audit trail persistence."""

import json

import boto3

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.ports.audit_repository import AuditRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBAuditRepository(AuditRepository):
    """Append-only audit trail in DynamoDB.

    Key schema:
        PK = CONSULTATION#{consultation_id}
        SK = AUDIT#{timestamp}#{event_id}
    """

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

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

        self._table.put_item(Item=item)

    def find_by_consultation(
        self, consultation_id: str
    ) -> list[AuditEvent]:
        response = self._table.query(
            KeyConditionExpression=(
                "PK = :pk AND begins_with(SK, :sk_prefix)"
            ),
            ExpressionAttributeValues={
                ":pk": f"CONSULTATION#{consultation_id}",
                ":sk_prefix": "AUDIT#",
            },
        )
        return [
            self._to_entity(item) for item in response.get("Items", [])
        ]

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
