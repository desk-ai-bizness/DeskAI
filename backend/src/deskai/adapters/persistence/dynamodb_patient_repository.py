"""DynamoDB adapter for patient persistence."""

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.adapters.persistence.schema import PatientFields as F
from deskai.domain.patient.entities import Patient
from deskai.ports.patient_repository import PatientRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class DynamoDBPatientRepository(DynamoDBBaseRepository, PatientRepository):
    """Persist and query patients in DynamoDB.

    Key schema:
        PK = CLINIC#{clinic_id}
        SK = PATIENT#{patient_id}
    """

    def save(self, patient: Patient) -> None:
        self._safe_put_item(
            Item={
                F.PK: f"CLINIC#{patient.clinic_id}",
                F.SK: f"PATIENT#{patient.patient_id}",
                F.PATIENT_ID: patient.patient_id,
                F.NAME: patient.name,
                F.DATE_OF_BIRTH: patient.date_of_birth,
                F.CLINIC_ID: patient.clinic_id,
                F.CREATED_AT: patient.created_at,
            }
        )
        logger.info(
            "dynamodb_patient_saved",
            extra=log_context(patient_id=patient.patient_id, clinic_id=patient.clinic_id),
        )

    def find_by_id(
        self, patient_id: str, clinic_id: str
    ) -> Patient | None:
        response = self._safe_get_item(
            Key={
                F.PK: f"CLINIC#{clinic_id}",
                F.SK: f"PATIENT#{patient_id}",
            },
        )
        item = response.get("Item")
        if item is None:
            logger.debug(
                "dynamodb_patient_not_found",
                extra=log_context(patient_id=patient_id, clinic_id=clinic_id),
            )
            return None
        logger.debug(
            "dynamodb_patient_found",
            extra=log_context(patient_id=patient_id, clinic_id=clinic_id),
        )
        return self._to_entity(item)

    def find_by_clinic(
        self, clinic_id: str, search_term: str = ""
    ) -> list[Patient]:
        items = self._paginated_query(
            KeyConditionExpression=(
                "PK = :pk AND begins_with(SK, :sk_prefix)"
            ),
            ExpressionAttributeValues={
                ":pk": f"CLINIC#{clinic_id}",
                ":sk_prefix": "PATIENT#",
            },
        )
        patients = [self._to_entity(item) for item in items]
        if search_term:
            term_lower = search_term.lower()
            patients = [
                p for p in patients if term_lower in p.name.lower()
            ]
        logger.debug(
            "dynamodb_patients_queried",
            extra=log_context(clinic_id=clinic_id, count=len(patients)),
        )
        return patients

    @staticmethod
    def _to_entity(item: dict) -> Patient:
        return Patient(
            patient_id=item[F.PATIENT_ID],
            name=item[F.NAME],
            date_of_birth=item[F.DATE_OF_BIRTH],
            clinic_id=item[F.CLINIC_ID],
            created_at=item[F.CREATED_AT],
        )
