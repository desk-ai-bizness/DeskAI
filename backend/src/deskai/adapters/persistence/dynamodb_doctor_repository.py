"""DynamoDB adapter for doctor profile persistence."""

from datetime import UTC, datetime

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.adapters.persistence.schema import DoctorProfileFields as F
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import PlanType
from deskai.ports.doctor_repository import DoctorRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class DynamoDBDoctorRepository(DynamoDBBaseRepository, DoctorRepository):
    """Resolve doctor profiles and consultation counts from DynamoDB."""

    def find_by_identity_provider_id(self, identity_provider_id: str) -> DoctorProfile | None:
        response = self._safe_get_item(
            Key={
                F.PK: f"DOCTOR#{identity_provider_id}",
                F.SK: "PROFILE",
            },
        )
        item = response.get("Item")
        logger.debug(
            "dynamodb_doctor_profile_lookup",
            extra=log_context(found=item is not None),
        )
        if item is None:
            return None

        return DoctorProfile(
            doctor_id=item[F.DOCTOR_ID],
            identity_provider_id=identity_provider_id,
            email=item[F.EMAIL],
            name=item.get(F.FULL_NAME) or item.get(F.LEGACY_NAME, ""),
            clinic_id=item[F.CLINIC_ID],
            clinic_name=item.get(F.CLINIC_NAME, ""),
            plan_type=PlanType(item[F.PLAN_TYPE]),
            created_at=datetime.fromisoformat(item[F.CREATED_AT]),
        )

    def count_consultations_this_month(self, doctor_id: str) -> int:
        now = datetime.now(tz=UTC)
        month_prefix = now.strftime("%Y-%m")

        response = self._safe_query(
            IndexName="gsi_doctor_date",
            Select="COUNT",
            KeyConditionExpression=("GSI1PK = :pk AND begins_with(GSI1SK, :sk_prefix)"),
            ExpressionAttributeValues={
                ":pk": f"DOCTOR#{doctor_id}",
                ":sk_prefix": f"CONSULTATION#{month_prefix}",
            },
        )
        count = response.get("Count", 0)
        logger.debug(
            "dynamodb_consultation_count",
            extra=log_context(doctor_id=doctor_id, month=month_prefix, count=count),
        )
        return count

    def find_created_at(self, doctor_id: str) -> datetime | None:
        response = self._safe_query(
            KeyConditionExpression=f"{F.PK} = :pk AND {F.SK} = :sk",
            ExpressionAttributeValues={
                ":pk": f"DOCTOR#{doctor_id}",
                ":sk": "PROFILE",
            },
            ProjectionExpression=F.CREATED_AT,
            Limit=1,
        )
        items = response.get("Items", [])
        if not items:
            return None
        raw = items[0].get(F.CREATED_AT)
        return datetime.fromisoformat(raw) if raw else None
