"""Unit tests for consultation patient-history queries."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_consultation_repository import (
    DynamoDBConsultationRepository,
)
from deskai.domain.consultation.entities import Consultation, ConsultationStatus


@patch("deskai.adapters.persistence.base_repository.boto3")
class DynamoDBPatientHistoryRepositoryTest(unittest.TestCase):
    def _make_repo(self, mock_boto3: MagicMock) -> DynamoDBConsultationRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBConsultationRepository(table_name="test-table")

    def test_save_adds_patient_history_gsi_keys(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        consultation = Consultation(
            consultation_id="cons-001",
            clinic_id="clinic-001",
            doctor_id="doc-001",
            patient_id="pat-001",
            specialty="general_practice",
            status=ConsultationStatus.STARTED,
            scheduled_date="2026-04-01",
            notes="",
            created_at="2026-04-01T10:00:00+00:00",
            updated_at="2026-04-01T10:00:00+00:00",
        )

        repo.save(consultation)

        item = self.mock_table.put_item.call_args.kwargs["Item"]
        self.assertEqual(item["GSI3PK"], "CLINIC#clinic-001#PATIENT#pat-001")
        self.assertEqual(item["GSI3SK"], "DOCTOR#doc-001#CONSULTATION#2026-04-01#cons-001")

    def test_find_by_patient_for_doctor_queries_gsi_patient(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "PK": "CLINIC#clinic-001",
                    "SK": "CONSULTATION#cons-001",
                    "GSI1PK": "DOCTOR#doc-001",
                    "GSI1SK": "CONSULTATION#2026-04-01#cons-001",
                    "GSI3PK": "CLINIC#clinic-001#PATIENT#pat-001",
                    "GSI3SK": "DOCTOR#doc-001#CONSULTATION#2026-04-01#cons-001",
                    "consultation_id": "cons-001",
                    "clinic_id": "clinic-001",
                    "doctor_id": "doc-001",
                    "patient_id": "pat-001",
                    "specialty": "general_practice",
                    "status": "finalized",
                    "scheduled_date": "2026-04-01",
                    "notes": "",
                    "created_at": "2026-04-01T10:00:00+00:00",
                    "updated_at": "2026-04-01T10:00:00+00:00",
                    "finalized_at": "2026-04-02T10:00:00+00:00",
                }
            ]
        }

        result = repo.find_by_patient_for_doctor(
            clinic_id="clinic-001",
            patient_id="pat-001",
            doctor_id="doc-001",
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].consultation_id, "cons-001")
        call_kwargs = self.mock_table.query.call_args.kwargs
        self.assertEqual(call_kwargs["IndexName"], "gsi_patient")
        self.assertEqual(
            call_kwargs["ExpressionAttributeValues"][":pk"],
            "CLINIC#clinic-001#PATIENT#pat-001",
        )
        self.assertEqual(
            call_kwargs["ExpressionAttributeValues"][":sk_prefix"],
            "DOCTOR#doc-001#CONSULTATION#",
        )


if __name__ == "__main__":
    unittest.main()
