"""Unit tests for the DynamoDB patient repository adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_patient_repository import (
    DynamoDBPatientRepository,
)
from deskai.domain.patient.entities import Patient


@patch("deskai.adapters.persistence.base_repository.boto3")
class DynamoDBPatientRepositoryTest(unittest.TestCase):
    def _make_repo(
        self, mock_boto3: MagicMock
    ) -> DynamoDBPatientRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBPatientRepository(table_name="test-table")

    # ---- save ----

    def test_save_puts_item_with_correct_pk_sk(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        patient = Patient(
            patient_id="pat-001",
            name="Maria Silva",
            date_of_birth="1990-05-15",
            clinic_id="clinic-01",
            created_at="2026-04-01T10:00:00Z",
        )

        repo.save(patient)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["PK"], "CLINIC#clinic-01")
        self.assertEqual(item["SK"], "PATIENT#pat-001")
        self.assertEqual(item["patient_id"], "pat-001")
        self.assertEqual(item["name"], "Maria Silva")
        self.assertEqual(item["date_of_birth"], "1990-05-15")
        self.assertEqual(item["clinic_id"], "clinic-01")
        self.assertEqual(item["created_at"], "2026-04-01T10:00:00Z")

    # ---- find_by_id ----

    def test_find_by_id_returns_patient_when_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {
            "Item": {
                "PK": "CLINIC#clinic-01",
                "SK": "PATIENT#pat-001",
                "patient_id": "pat-001",
                "name": "Maria Silva",
                "date_of_birth": "1990-05-15",
                "clinic_id": "clinic-01",
                "created_at": "2026-04-01T10:00:00Z",
            }
        }

        result = repo.find_by_id("pat-001", clinic_id="clinic-01")

        self.assertIsNotNone(result)
        self.assertEqual(result.patient_id, "pat-001")
        self.assertEqual(result.name, "Maria Silva")
        self.assertEqual(result.date_of_birth, "1990-05-15")
        self.assertEqual(result.clinic_id, "clinic-01")
        self.mock_table.get_item.assert_called_once_with(
            Key={
                "PK": "CLINIC#clinic-01",
                "SK": "PATIENT#pat-001",
            }
        )

    def test_find_by_id_returns_none_when_not_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {}

        result = repo.find_by_id("pat-missing", clinic_id="clinic-01")

        self.assertIsNone(result)

    # ---- find_by_clinic ----

    def test_find_by_clinic_queries_with_begins_with(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "patient_id": "pat-001",
                    "name": "Maria Silva",
                    "date_of_birth": "1990-05-15",
                    "clinic_id": "clinic-01",
                    "created_at": "2026-04-01T10:00:00Z",
                },
            ]
        }

        result = repo.find_by_clinic("clinic-01")

        call_kwargs = self.mock_table.query.call_args[1]
        self.assertIn("CLINIC#clinic-01", str(call_kwargs))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].patient_id, "pat-001")

    def test_find_by_clinic_with_search_term_filters_by_name(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "patient_id": "pat-001",
                    "name": "Maria Silva",
                    "date_of_birth": "1990-05-15",
                    "clinic_id": "clinic-01",
                    "created_at": "2026-04-01T10:00:00Z",
                },
                {
                    "patient_id": "pat-002",
                    "name": "Joao Santos",
                    "date_of_birth": "1985-03-20",
                    "clinic_id": "clinic-01",
                    "created_at": "2026-04-01T11:00:00Z",
                },
            ]
        }

        result = repo.find_by_clinic("clinic-01", search_term="maria")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Maria Silva")

    def test_find_by_clinic_returns_empty_list(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}

        result = repo.find_by_clinic("clinic-empty")

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
