"""DynamoDB adapter for session persistence."""

import boto3

from deskai.domain.session.entities import Session, SessionState
from deskai.ports.session_repository import SessionRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBSessionRepository(SessionRepository):
    """Persist and query sessions in DynamoDB.

    Key schema:
        PK = SESSION#{session_id}
        SK = METADATA

    GSI consultation-session-index:
        GSI1PK = CONSULTATION#{consultation_id}
        GSI1SK = SESSION#{session_id}
    """

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def save(self, session: Session) -> None:
        self._table.put_item(Item=self._to_item(session))

    def find_by_id(self, session_id: str) -> Session | None:
        response = self._table.get_item(
            Key={"PK": f"SESSION#{session_id}", "SK": "METADATA"},
        )
        item = response.get("Item")
        if item is None:
            return None
        return self._to_entity(item)

    def find_active_by_consultation_id(
        self, consultation_id: str
    ) -> Session | None:
        response = self._table.query(
            IndexName="consultation-session-index",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"CONSULTATION#{consultation_id}",
            },
        )
        items = response.get("Items", [])
        if not items:
            return None
        return self._to_entity(items[0])

    def update(self, session: Session) -> None:
        self._table.put_item(Item=self._to_item(session))

    def delete(self, session_id: str) -> None:
        self._table.delete_item(
            Key={"PK": f"SESSION#{session_id}", "SK": "METADATA"},
        )

    @staticmethod
    def _to_item(session: Session) -> dict:
        item: dict[str, object] = {
            "PK": f"SESSION#{session.session_id}",
            "SK": "METADATA",
            "GSI1PK": f"CONSULTATION#{session.consultation_id}",
            "GSI1SK": f"SESSION#{session.session_id}",
            "session_id": session.session_id,
            "consultation_id": session.consultation_id,
            "doctor_id": session.doctor_id,
            "clinic_id": session.clinic_id,
            "state": str(session.state),
            "started_at": session.started_at,
            "audio_chunks_received": session.audio_chunks_received,
            "duration_seconds": session.duration_seconds,
        }

        optional_fields = (
            "connection_id",
            "ended_at",
            "grace_period_expires_at",
            "last_activity_at",
        )
        for field in optional_fields:
            value = getattr(session, field)
            if value is not None:
                item[field] = value

        return item

    @staticmethod
    def _to_entity(item: dict) -> Session:
        return Session(
            session_id=item["session_id"],
            consultation_id=item["consultation_id"],
            doctor_id=item["doctor_id"],
            clinic_id=item["clinic_id"],
            connection_id=item.get("connection_id"),
            state=SessionState(item["state"]),
            started_at=item.get("started_at", ""),
            ended_at=item.get("ended_at"),
            duration_seconds=int(item.get("duration_seconds", 0)),
            audio_chunks_received=int(item.get("audio_chunks_received", 0)),
            grace_period_expires_at=item.get("grace_period_expires_at"),
            last_activity_at=item.get("last_activity_at"),
        )
