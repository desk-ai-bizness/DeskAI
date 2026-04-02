"""Unit tests for the DynamoDB consultation repository adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_consultation_repository import (
    DynamoDBConsultationRepository,
)
from deskai.domain.consultation.entities import Consultation, ConsultationStatus


@patch("deskai.adapters.persistence.dynamodb_consultation_repository.boto3")
class DynamoDBConsultationRepositoryTest(unittest.TestCase):
    def _make_repo(
        self, mock_boto3: MagicMock
    ) -> DynamoDBConsultationRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBConsultationRepository(table_name="test-table")

    # ---- save ----

    def test_save_puts_item_with_correct_pk_sk(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        consultation = Consultation(
            consultation_id="cons-001",
            clinic_id="clinic-01",
            doctor_id="doc-01",
            patient_id="pat-01",
            specialty="general_practice",
            status=ConsultationStatus.STARTED,
            scheduled_date="2026-04-02",
            created_at="2026-04-02T10:00:00Z",
            updated_at="2026-04-02T10:00:00Z",
        )

        repo.save(consultation)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["PK"], "CLINIC#clinic-01")
        self.assertEqual(item["SK"], "CONSULTATION#cons-001")

    def test_save_includes_gsi_attributes(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        consultation = Consultation(
            consultation_id="cons-002",
            clinic_id="clinic-01",
            doctor_id="doc-07",
            patient_id="pat-01",
            specialty="general_practice",
            scheduled_date="2026-04-05",
            created_at="2026-04-02T10:00:00Z",
            updated_at="2026-04-02T10:00:00Z",
        )

        repo.save(consultation)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["GSI1PK"], "DOCTOR#doc-07")
        self.assertEqual(
            item["GSI1SK"], "CONSULTATION#2026-04-05#cons-002"
        )

    def test_save_stores_all_consultation_fields(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        consultation = Consultation(
            consultation_id="cons-003",
            clinic_id="clinic-02",
            doctor_id="doc-03",
            patient_id="pat-05",
            specialty="general_practice",
            status=ConsultationStatus.RECORDING,
            scheduled_date="2026-04-10",
            notes="initial notes",
            created_at="2026-04-02T08:00:00Z",
            updated_at="2026-04-02T08:30:00Z",
            session_started_at="2026-04-02T08:15:00Z",
        )

        repo.save(consultation)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["consultation_id"], "cons-003")
        self.assertEqual(item["clinic_id"], "clinic-02")
        self.assertEqual(item["doctor_id"], "doc-03")
        self.assertEqual(item["patient_id"], "pat-05")
        self.assertEqual(item["specialty"], "general_practice")
        self.assertEqual(item["status"], "recording")
        self.assertEqual(item["scheduled_date"], "2026-04-10")
        self.assertEqual(item["notes"], "initial notes")
        self.assertEqual(item["created_at"], "2026-04-02T08:00:00Z")
        self.assertEqual(item["updated_at"], "2026-04-02T08:30:00Z")
        self.assertEqual(
            item["session_started_at"], "2026-04-02T08:15:00Z"
        )

    # ---- find_by_id ----

    def test_find_by_id_returns_consultation_when_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {
            "Item": {
                "PK": "CLINIC#clinic-01",
                "SK": "CONSULTATION#cons-001",
                "consultation_id": "cons-001",
                "clinic_id": "clinic-01",
                "doctor_id": "doc-01",
                "patient_id": "pat-01",
                "specialty": "general_practice",
                "status": "started",
                "scheduled_date": "2026-04-02",
                "notes": "",
                "created_at": "2026-04-02T10:00:00Z",
                "updated_at": "2026-04-02T10:00:00Z",
            }
        }

        result = repo.find_by_id("cons-001", clinic_id="clinic-01")

        self.assertIsNotNone(result)
        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.clinic_id, "clinic-01")
        self.assertEqual(result.doctor_id, "doc-01")
        self.assertEqual(result.status, ConsultationStatus.STARTED)
        self.mock_table.get_item.assert_called_once_with(
            Key={
                "PK": "CLINIC#clinic-01",
                "SK": "CONSULTATION#cons-001",
            }
        )

    def test_find_by_id_returns_none_when_not_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {}

        result = repo.find_by_id("cons-missing", clinic_id="clinic-01")

        self.assertIsNone(result)

    # ---- find_by_doctor_and_date_range ----

    def test_find_by_doctor_and_date_range_queries_gsi(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}

        repo.find_by_doctor_and_date_range(
            "doc-01", "2026-04-01", "2026-04-30"
        )

        call_kwargs = self.mock_table.query.call_args[1]
        self.assertEqual(call_kwargs["IndexName"], "gsi_doctor_date")
        self.assertEqual(
            call_kwargs["ExpressionAttributeValues"][":pk"],
            "DOCTOR#doc-01",
        )
        self.assertEqual(
            call_kwargs["ExpressionAttributeValues"][":sk_start"],
            "CONSULTATION#2026-04-01",
        )
        self.assertEqual(
            call_kwargs["ExpressionAttributeValues"][":sk_end"],
            "CONSULTATION#2026-04-30\uffff",
        )

    def test_find_by_doctor_and_date_range_returns_empty_list(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}

        result = repo.find_by_doctor_and_date_range(
            "doc-01", "2026-04-01", "2026-04-30"
        )

        self.assertEqual(result, [])

    def test_find_by_doctor_and_date_range_deserializes_items(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "consultation_id": "cons-a",
                    "clinic_id": "clinic-01",
                    "doctor_id": "doc-01",
                    "patient_id": "pat-01",
                    "specialty": "general_practice",
                    "status": "started",
                    "scheduled_date": "2026-04-05",
                    "notes": "",
                    "created_at": "2026-04-01T09:00:00Z",
                    "updated_at": "2026-04-01T09:00:00Z",
                },
                {
                    "consultation_id": "cons-b",
                    "clinic_id": "clinic-01",
                    "doctor_id": "doc-01",
                    "patient_id": "pat-02",
                    "specialty": "general_practice",
                    "status": "finalized",
                    "scheduled_date": "2026-04-10",
                    "notes": "follow up",
                    "created_at": "2026-04-05T14:00:00Z",
                    "updated_at": "2026-04-10T16:00:00Z",
                    "finalized_at": "2026-04-10T16:00:00Z",
                    "finalized_by": "doc-01",
                },
            ]
        }

        result = repo.find_by_doctor_and_date_range(
            "doc-01", "2026-04-01", "2026-04-30"
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].consultation_id, "cons-a")
        self.assertEqual(result[1].consultation_id, "cons-b")
        self.assertEqual(result[1].status, ConsultationStatus.FINALIZED)
        self.assertEqual(result[1].finalized_by, "doc-01")

    # ---- update_status ----

    def test_update_status_updates_item(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)

        repo.update_status(
            "cons-001",
            ConsultationStatus.RECORDING,
            clinic_id="clinic-01",
        )

        call_kwargs = self.mock_table.update_item.call_args[1]
        self.assertEqual(
            call_kwargs["Key"],
            {
                "PK": "CLINIC#clinic-01",
                "SK": "CONSULTATION#cons-001",
            },
        )
        self.assertIn(":status", call_kwargs["ExpressionAttributeValues"])
        self.assertEqual(
            call_kwargs["ExpressionAttributeValues"][":status"],
            "recording",
        )

    def test_update_status_with_extra_kwargs(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)

        repo.update_status(
            "cons-001",
            ConsultationStatus.FINALIZED,
            clinic_id="clinic-01",
            finalized_at="2026-04-02T18:00:00Z",
            finalized_by="doc-01",
        )

        call_kwargs = self.mock_table.update_item.call_args[1]
        values = call_kwargs["ExpressionAttributeValues"]
        self.assertEqual(values[":status"], "finalized")
        self.assertEqual(
            values[":finalized_at"], "2026-04-02T18:00:00Z"
        )
        self.assertEqual(values[":finalized_by"], "doc-01")


if __name__ == "__main__":
    unittest.main()
