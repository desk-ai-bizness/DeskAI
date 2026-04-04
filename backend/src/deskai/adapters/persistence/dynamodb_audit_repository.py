"""DynamoDB adapter for audit trail persistence."""

import json

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.adapters.persistence.schema import AuditFields as F
from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.ports.audit_repository import AuditRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class DynamoDBAuditRepository(DynamoDBBaseRepository, AuditRepository):
    """Append-only audit trail in DynamoDB.

    Key schema:
        PK = CONSULTATION#{consultation_id}
        SK = AUDIT#{timestamp}#{event_id}
    """

    def append(self, event: AuditEvent) -> None:
        item: dict[str, object] = {
            F.PK: f"CONSULTATION#{event.consultation_id}",
            F.SK: f"AUDIT#{event.timestamp}#{event.event_id}",
            F.EVENT_ID: event.event_id,
            F.CONSULTATION_ID: event.consultation_id,
            F.EVENT_TYPE: str(event.event_type),
            F.ACTOR_ID: event.actor_id,
            F.TIMESTAMP: event.timestamp,
        }
        if event.payload is not None:
            item[F.PAYLOAD] = json.dumps(event.payload)

        self._safe_put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )
        logger.info(
            "dynamodb_audit_event_appended",
            extra=log_context(
                event_id=event.event_id,
                consultation_id=event.consultation_id,
                event_type=str(event.event_type),
                actor_id=event.actor_id,
            ),
        )

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
        logger.debug(
            "dynamodb_audit_events_queried",
            extra=log_context(consultation_id=consultation_id, count=len(items)),
        )
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_entity(item: dict) -> AuditEvent:
        raw_payload = item.get(F.PAYLOAD)
        payload = json.loads(raw_payload) if raw_payload else None

        return AuditEvent(
            event_id=item[F.EVENT_ID],
            consultation_id=item[F.CONSULTATION_ID],
            event_type=AuditAction(item[F.EVENT_TYPE]),
            actor_id=item[F.ACTOR_ID],
            timestamp=item[F.TIMESTAMP],
            payload=payload,
        )
