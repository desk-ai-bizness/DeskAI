"""DynamoDB adapter for consultation persistence."""

from datetime import UTC, datetime

import boto3

from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBConsultationRepository(ConsultationRepository):
    """Persist and query consultations in DynamoDB.

    Key schema:
        PK = CLINIC#{clinic_id}
        SK = CONSULTATION#{consultation_id}

    GSI gsi_doctor_date:
        GSI1PK = DOCTOR#{doctor_id}
        GSI1SK = CONSULTATION#{scheduled_date}#{consultation_id}
    """

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def save(self, consultation: Consultation) -> None:
        item = {
            "PK": f"CLINIC#{consultation.clinic_id}",
            "SK": f"CONSULTATION#{consultation.consultation_id}",
            "GSI1PK": f"DOCTOR#{consultation.doctor_id}",
            "GSI1SK": (
                f"CONSULTATION#{consultation.scheduled_date}"
                f"#{consultation.consultation_id}"
            ),
            "consultation_id": consultation.consultation_id,
            "clinic_id": consultation.clinic_id,
            "doctor_id": consultation.doctor_id,
            "patient_id": consultation.patient_id,
            "specialty": consultation.specialty,
            "status": str(consultation.status),
            "scheduled_date": consultation.scheduled_date,
            "notes": consultation.notes,
            "created_at": consultation.created_at,
            "updated_at": consultation.updated_at,
        }

        optional_fields = (
            "session_started_at",
            "session_ended_at",
            "processing_started_at",
            "processing_completed_at",
            "review_opened_at",
            "finalized_at",
            "finalized_by",
            "error_details",
        )
        for field in optional_fields:
            value = getattr(consultation, field)
            if value is not None:
                item[field] = value

        self._table.put_item(Item=item)

    def find_by_id(
        self, consultation_id: str, clinic_id: str
    ) -> Consultation | None:
        response = self._table.get_item(
            Key={
                "PK": f"CLINIC#{clinic_id}",
                "SK": f"CONSULTATION#{consultation_id}",
            },
        )
        item = response.get("Item")
        if item is None:
            return None
        return self._to_entity(item)

    def find_by_doctor_and_date_range(
        self, doctor_id: str, start_date: str, end_date: str
    ) -> list[Consultation]:
        response = self._table.query(
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
        return [self._to_entity(item) for item in response.get("Items", [])]

    def update_status(
        self,
        consultation_id: str,
        new_status: ConsultationStatus,
        **kwargs: object,
    ) -> None:
        clinic_id = kwargs.pop("clinic_id", "")
        now = datetime.now(tz=UTC).isoformat()

        update_parts = ["#st = :status", "updated_at = :updated_at"]
        attr_values: dict[str, object] = {
            ":status": str(new_status),
            ":updated_at": now,
        }
        attr_names = {"#st": "status"}

        for key, value in kwargs.items():
            placeholder = f":{key}"
            update_parts.append(f"{key} = {placeholder}")
            attr_values[placeholder] = value

        self._table.update_item(
            Key={
                "PK": f"CLINIC#{clinic_id}",
                "SK": f"CONSULTATION#{consultation_id}",
            },
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeValues=attr_values,
            ExpressionAttributeNames=attr_names,
        )

    @staticmethod
    def _to_entity(item: dict) -> Consultation:
        return Consultation(
            consultation_id=item["consultation_id"],
            clinic_id=item["clinic_id"],
            doctor_id=item["doctor_id"],
            patient_id=item["patient_id"],
            specialty=item["specialty"],
            status=ConsultationStatus(item["status"]),
            scheduled_date=item.get("scheduled_date", ""),
            notes=item.get("notes", ""),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
            session_started_at=item.get("session_started_at"),
            session_ended_at=item.get("session_ended_at"),
            processing_started_at=item.get("processing_started_at"),
            processing_completed_at=item.get("processing_completed_at"),
            review_opened_at=item.get("review_opened_at"),
            finalized_at=item.get("finalized_at"),
            finalized_by=item.get("finalized_by"),
            error_details=item.get("error_details"),
        )
