"""DynamoDB adapter for patient persistence."""

import boto3

from deskai.domain.patient.entities import Patient
from deskai.ports.patient_repository import PatientRepository
from deskai.shared.logging import get_logger

logger = get_logger()


class DynamoDBPatientRepository(PatientRepository):
    """Persist and query patients in DynamoDB.

    Key schema:
        PK = CLINIC#{clinic_id}
        SK = PATIENT#{patient_id}
    """

    def __init__(self, table_name: str) -> None:
        self._table_name = table_name
        dynamodb = boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def save(self, patient: Patient) -> None:
        self._table.put_item(
            Item={
                "PK": f"CLINIC#{patient.clinic_id}",
                "SK": f"PATIENT#{patient.patient_id}",
                "patient_id": patient.patient_id,
                "name": patient.name,
                "date_of_birth": patient.date_of_birth,
                "clinic_id": patient.clinic_id,
                "created_at": patient.created_at,
            }
        )

    def find_by_id(
        self, patient_id: str, clinic_id: str
    ) -> Patient | None:
        response = self._table.get_item(
            Key={
                "PK": f"CLINIC#{clinic_id}",
                "SK": f"PATIENT#{patient_id}",
            },
        )
        item = response.get("Item")
        if item is None:
            return None
        return self._to_entity(item)

    def find_by_clinic(
        self, clinic_id: str, search_term: str = ""
    ) -> list[Patient]:
        response = self._table.query(
            KeyConditionExpression=(
                "PK = :pk AND begins_with(SK, :sk_prefix)"
            ),
            ExpressionAttributeValues={
                ":pk": f"CLINIC#{clinic_id}",
                ":sk_prefix": "PATIENT#",
            },
        )
        patients = [
            self._to_entity(item) for item in response.get("Items", [])
        ]
        if search_term:
            term_lower = search_term.lower()
            patients = [
                p for p in patients if term_lower in p.name.lower()
            ]
        return patients

    @staticmethod
    def _to_entity(item: dict) -> Patient:
        return Patient(
            patient_id=item["patient_id"],
            name=item["name"],
            date_of_birth=item["date_of_birth"],
            clinic_id=item["clinic_id"],
            created_at=item["created_at"],
        )
