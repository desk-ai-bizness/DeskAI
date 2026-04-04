"""DynamoDB adapter for consultation persistence."""

from datetime import UTC, datetime

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.adapters.persistence.schema import ConsultationFields as F
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class DynamoDBConsultationRepository(DynamoDBBaseRepository, ConsultationRepository):
    """Persist and query consultations in DynamoDB.

    Key schema:
        PK = CLINIC#{clinic_id}
        SK = CONSULTATION#{consultation_id}

    GSI gsi_doctor_date:
        GSI1PK = DOCTOR#{doctor_id}
        GSI1SK = CONSULTATION#{scheduled_date}#{consultation_id}
    """

    def save(self, consultation: Consultation) -> None:
        item: dict[str, object] = {
            F.PK: f"CLINIC#{consultation.clinic_id}",
            F.SK: f"CONSULTATION#{consultation.consultation_id}",
            F.GSI1PK: f"DOCTOR#{consultation.doctor_id}",
            F.GSI1SK: (
                f"CONSULTATION#{consultation.scheduled_date}"
                f"#{consultation.consultation_id}"
            ),
            F.CONSULTATION_ID: consultation.consultation_id,
            F.CLINIC_ID: consultation.clinic_id,
            F.DOCTOR_ID: consultation.doctor_id,
            F.PATIENT_ID: consultation.patient_id,
            F.SPECIALTY: consultation.specialty,
            F.STATUS: str(consultation.status),
            F.SCHEDULED_DATE: consultation.scheduled_date,
            F.NOTES: consultation.notes,
            F.CREATED_AT: consultation.created_at,
            F.UPDATED_AT: consultation.updated_at,
        }

        optional_fields = (
            (F.SESSION_STARTED_AT, "session_started_at"),
            (F.SESSION_ENDED_AT, "session_ended_at"),
            (F.PROCESSING_STARTED_AT, "processing_started_at"),
            (F.PROCESSING_COMPLETED_AT, "processing_completed_at"),
            (F.REVIEW_OPENED_AT, "review_opened_at"),
            (F.FINALIZED_AT, "finalized_at"),
            (F.FINALIZED_BY, "finalized_by"),
            (F.ERROR_DETAILS, "error_details"),
        )
        for key, attr in optional_fields:
            value = getattr(consultation, attr)
            if value is not None:
                item[key] = value

        self._safe_put_item(Item=item)
        logger.info(
            "dynamodb_consultation_saved",
            extra=log_context(
                consultation_id=consultation.consultation_id,
                clinic_id=consultation.clinic_id,
                status=str(consultation.status),
            ),
        )

    def find_by_id(
        self, consultation_id: str, clinic_id: str
    ) -> Consultation | None:
        response = self._safe_get_item(
            Key={
                F.PK: f"CLINIC#{clinic_id}",
                F.SK: f"CONSULTATION#{consultation_id}",
            },
        )
        item = response.get("Item")
        if item is None:
            logger.debug(
                "dynamodb_consultation_not_found",
                extra=log_context(consultation_id=consultation_id, clinic_id=clinic_id),
            )
            return None
        logger.debug(
            "dynamodb_consultation_found",
            extra=log_context(consultation_id=consultation_id, clinic_id=clinic_id),
        )
        return self._to_entity(item)

    def find_by_doctor_and_date_range(
        self, doctor_id: str, start_date: str, end_date: str
    ) -> list[Consultation]:
        response = self._safe_query(
            IndexName="gsi_doctor_date",
            KeyConditionExpression=(
                "GSI1PK = :pk"
                " AND GSI1SK BETWEEN :sk_start AND :sk_end"
            ),
            ExpressionAttributeValues={
                ":pk": f"DOCTOR#{doctor_id}",
                ":sk_start": f"CONSULTATION#{start_date}",
                ":sk_end": f"CONSULTATION#{end_date}\uffff",
            },
        )
        results = [self._to_entity(item) for item in response.get("Items", [])]
        logger.debug(
            "dynamodb_consultations_queried",
            extra=log_context(
                doctor_id=doctor_id, start_date=start_date, end_date=end_date, count=len(results),
            ),
        )
        return results

    def update_status(
        self,
        consultation_id: str,
        new_status: ConsultationStatus,
        **kwargs: object,
    ) -> None:
        clinic_id = kwargs.pop("clinic_id", "")
        now = datetime.now(tz=UTC).isoformat()

        update_parts = ["#st = :status", f"{F.UPDATED_AT} = :updated_at"]
        attr_values: dict[str, object] = {
            ":status": str(new_status),
            ":updated_at": now,
        }
        attr_names = {"#st": F.STATUS}

        for key, value in kwargs.items():
            placeholder = f":{key}"
            update_parts.append(f"{key} = {placeholder}")
            attr_values[placeholder] = value

        self._safe_update_item(
            Key={
                F.PK: f"CLINIC#{clinic_id}",
                F.SK: f"CONSULTATION#{consultation_id}",
            },
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeValues=attr_values,
            ExpressionAttributeNames=attr_names,
        )
        logger.info(
            "dynamodb_consultation_status_updated",
            extra=log_context(
                consultation_id=consultation_id, new_status=str(new_status), clinic_id=clinic_id,
            ),
        )

    @staticmethod
    def _to_entity(item: dict) -> Consultation:
        return Consultation(
            consultation_id=item[F.CONSULTATION_ID],
            clinic_id=item[F.CLINIC_ID],
            doctor_id=item[F.DOCTOR_ID],
            patient_id=item[F.PATIENT_ID],
            specialty=item[F.SPECIALTY],
            status=ConsultationStatus(item[F.STATUS]),
            scheduled_date=item.get(F.SCHEDULED_DATE, ""),
            notes=item.get(F.NOTES, ""),
            created_at=item.get(F.CREATED_AT, ""),
            updated_at=item.get(F.UPDATED_AT, ""),
            session_started_at=item.get(F.SESSION_STARTED_AT),
            session_ended_at=item.get(F.SESSION_ENDED_AT),
            processing_started_at=item.get(F.PROCESSING_STARTED_AT),
            processing_completed_at=item.get(F.PROCESSING_COMPLETED_AT),
            review_opened_at=item.get(F.REVIEW_OPENED_AT),
            finalized_at=item.get(F.FINALIZED_AT),
            finalized_by=item.get(F.FINALIZED_BY),
            error_details=item.get(F.ERROR_DETAILS),
        )
