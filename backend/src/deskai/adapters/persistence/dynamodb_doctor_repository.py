"""DynamoDB adapter for doctor profile persistence."""

from datetime import UTC, datetime

import boto3

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import PlanType
from deskai.ports.doctor_repository import DoctorRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBDoctorRepository(DoctorRepository):
    """Resolve doctor profiles and consultation counts from DynamoDB."""

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def find_by_cognito_sub(
        self, cognito_sub: str
    ) -> DoctorProfile | None:
        response = self._table.get_item(
            Key={
                "PK": f"DOCTOR#{cognito_sub}",
                "SK": "PROFILE",
            },
        )
        item = response.get("Item")
        if item is None:
            return None

        return DoctorProfile(
            doctor_id=item["doctor_id"],
            cognito_sub=cognito_sub,
            email=item["email"],
            name=item["name"],
            clinic_id=item["clinic_id"],
            clinic_name=item["clinic_name"],
            plan_type=PlanType(item["plan_type"]),
            created_at=item["created_at"],
        )

    def count_consultations_this_month(
        self, doctor_id: str
    ) -> int:
        now = datetime.now(tz=UTC)
        month_prefix = now.strftime("%Y-%m")

        response = self._table.query(
            IndexName="gsi_doctor_date",
            Select="COUNT",
            KeyConditionExpression=(
                "GSI1PK = :pk"
                " AND begins_with(GSI1SK, :sk_prefix)"
            ),
            ExpressionAttributeValues={
                ":pk": f"DOCTOR#{doctor_id}",
                ":sk_prefix": f"CONSULTATION#{month_prefix}",
            },
        )
        return response.get("Count", 0)
