"""DynamoDB adapter for session persistence."""

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.adapters.persistence.schema import SessionFields as F
from deskai.domain.session.entities import Session, SessionState
from deskai.ports.session_repository import SessionRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class DynamoDBSessionRepository(DynamoDBBaseRepository, SessionRepository):
    """Persist and query sessions in DynamoDB.

    Key schema:
        PK = SESSION#{session_id}
        SK = METADATA

    GSI gsi_consultation_session:
        GSI4PK = CONSULTATION#{consultation_id}
        GSI4SK = SESSION#{session_id}
    """

    def save(self, session: Session) -> None:
        self._safe_put_item(Item=self._to_item(session))
        logger.info(
            "dynamodb_session_saved",
            extra=log_context(
                session_id=session.session_id,
                consultation_id=session.consultation_id,
                state=str(session.state),
            ),
        )

    def find_by_id(self, session_id: str) -> Session | None:
        response = self._safe_get_item(
            Key={F.PK: f"SESSION#{session_id}", F.SK: "METADATA"},
        )
        item = response.get("Item")
        if item is None:
            logger.debug(
                "dynamodb_session_not_found",
                extra=log_context(session_id=session_id),
            )
            return None
        logger.debug(
            "dynamodb_session_found",
            extra=log_context(session_id=session_id),
        )
        return self._to_entity(item)

    def find_active_by_consultation_id(self, consultation_id: str) -> Session | None:
        response = self._safe_query(
            IndexName="gsi_consultation_session",
            KeyConditionExpression="GSI4PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"CONSULTATION#{consultation_id}",
            },
        )
        items = response.get("Items", [])
        found = bool(items)
        logger.debug(
            "dynamodb_active_session_lookup",
            extra=log_context(consultation_id=consultation_id, found=found),
        )
        if not items:
            return None
        return self._to_entity(items[0])

    def update(self, session: Session) -> None:
        self._safe_put_item(Item=self._to_item(session))
        logger.debug(
            "dynamodb_session_updated",
            extra=log_context(session_id=session.session_id, state=str(session.state)),
        )

    def delete(self, session_id: str) -> None:
        self._safe_delete_item(
            Key={F.PK: f"SESSION#{session_id}", F.SK: "METADATA"},
        )
        logger.info("dynamodb_session_deleted", extra=log_context(session_id=session_id))

    @staticmethod
    def _to_item(session: Session) -> dict:
        item: dict[str, object] = {
            F.PK: f"SESSION#{session.session_id}",
            F.SK: "METADATA",
            F.GSI4PK: f"CONSULTATION#{session.consultation_id}",
            F.GSI4SK: f"SESSION#{session.session_id}",
            F.SESSION_ID: session.session_id,
            F.CONSULTATION_ID: session.consultation_id,
            F.DOCTOR_ID: session.doctor_id,
            F.CLINIC_ID: session.clinic_id,
            F.STATE: str(session.state),
            F.STARTED_AT: session.started_at,
            F.AUDIO_CHUNKS_RECEIVED: session.audio_chunks_received,
            F.DURATION_SECONDS: session.duration_seconds,
        }

        optional_fields = (
            (F.CONNECTION_ID, "connection_id"),
            (F.ENDED_AT, "ended_at"),
            (F.GRACE_PERIOD_EXPIRES_AT, "grace_period_expires_at"),
            (F.LAST_ACTIVITY_AT, "last_activity_at"),
        )
        for key, attr in optional_fields:
            value = getattr(session, attr)
            if value is not None:
                item[key] = value

        return item

    @staticmethod
    def _to_entity(item: dict) -> Session:
        return Session(
            session_id=item[F.SESSION_ID],
            consultation_id=item[F.CONSULTATION_ID],
            doctor_id=item[F.DOCTOR_ID],
            clinic_id=item[F.CLINIC_ID],
            connection_id=item.get(F.CONNECTION_ID),
            state=SessionState(item[F.STATE]),
            started_at=item.get(F.STARTED_AT, ""),
            ended_at=item.get(F.ENDED_AT),
            duration_seconds=int(item.get(F.DURATION_SECONDS, 0)),
            audio_chunks_received=int(item.get(F.AUDIO_CHUNKS_RECEIVED, 0)),
            grace_period_expires_at=item.get(F.GRACE_PERIOD_EXPIRES_AT),
            last_activity_at=item.get(F.LAST_ACTIVITY_AT),
        )
