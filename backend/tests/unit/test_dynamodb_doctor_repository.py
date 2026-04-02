"""Unit tests for the DynamoDB doctor repository adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_doctor_repository import (
    DynamoDBDoctorRepository,
)
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import PlanType


@patch("deskai.adapters.persistence.dynamodb_doctor_repository.boto3")
class DynamoDBDoctorRepositoryTest(unittest.TestCase):
    def _make_repo(
        self, mock_boto3: MagicMock
    ) -> DynamoDBDoctorRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBDoctorRepository(table_name="deskai-doctors")

    # --- find_by_cognito_sub ---

    def test_find_by_cognito_sub_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {
            "Item": {
                "doctor_id": "doc-001",
                "email": "ana@clinic.com",
                "name": "Dra. Ana",
                "clinic_id": "clinic-01",
                "clinic_name": "Clinica Vida",
                "plan_type": "plus",
                "created_at": "2025-01-15T10:00:00Z",
            }
        }

        result = repo.find_by_cognito_sub("sub-abc-123")

        self.assertEqual(
            result,
            DoctorProfile(
                doctor_id="doc-001",
                cognito_sub="sub-abc-123",
                email="ana@clinic.com",
                name="Dra. Ana",
                clinic_id="clinic-01",
                clinic_name="Clinica Vida",
                plan_type=PlanType.PLUS,
                created_at="2025-01-15T10:00:00Z",
            ),
        )
        self.mock_table.get_item.assert_called_once_with(
            Key={
                "PK": "DOCTOR#sub-abc-123",
                "SK": "PROFILE",
            }
        )

    def test_find_by_cognito_sub_not_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {}

        result = repo.find_by_cognito_sub("sub-missing")

        self.assertIsNone(result)

    def test_find_by_cognito_sub_parses_all_fields(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {
            "Item": {
                "doctor_id": "doc-99",
                "email": "carlos@saude.com",
                "name": "Dr. Carlos",
                "clinic_id": "clinic-77",
                "clinic_name": "Centro Saude",
                "plan_type": "pro",
                "created_at": "2024-06-01T08:30:00Z",
            }
        }

        result = repo.find_by_cognito_sub("sub-xyz-999")

        self.assertIsNotNone(result)
        self.assertEqual(result.doctor_id, "doc-99")
        self.assertEqual(result.cognito_sub, "sub-xyz-999")
        self.assertEqual(result.email, "carlos@saude.com")
        self.assertEqual(result.name, "Dr. Carlos")
        self.assertEqual(result.clinic_id, "clinic-77")
        self.assertEqual(result.clinic_name, "Centro Saude")
        self.assertEqual(result.plan_type, PlanType.PRO)
        self.assertEqual(
            result.created_at, "2024-06-01T08:30:00Z"
        )

    def test_find_by_cognito_sub_free_trial_plan(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {
            "Item": {
                "doctor_id": "doc-ft",
                "email": "trial@clinic.com",
                "name": "Dr. Trial",
                "clinic_id": "clinic-ft",
                "clinic_name": "Free Clinic",
                "plan_type": "free_trial",
                "created_at": "2025-03-01T00:00:00Z",
            }
        }

        result = repo.find_by_cognito_sub("sub-trial")

        self.assertEqual(result.plan_type, PlanType.FREE_TRIAL)

    # --- count_consultations_this_month ---

    def test_count_consultations_this_month(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Count": 42}

        result = repo.count_consultations_this_month("doc-001")

        self.assertEqual(result, 42)
        call_kwargs = self.mock_table.query.call_args[1]
        self.assertEqual(call_kwargs["IndexName"], "gsi_doctor_date")
        self.assertEqual(call_kwargs["Select"], "COUNT")
        self.assertEqual(
            call_kwargs["ExpressionAttributeValues"][":pk"],
            "DOCTOR#doc-001",
        )
        self.assertTrue(
            call_kwargs["ExpressionAttributeValues"][
                ":sk_prefix"
            ].startswith("CONSULTATION#")
        )

    def test_count_consultations_this_month_zero(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Count": 0}

        result = repo.count_consultations_this_month("doc-new")

        self.assertEqual(result, 0)

    def test_count_consultations_missing_count_key(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {}

        result = repo.count_consultations_this_month("doc-001")

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
