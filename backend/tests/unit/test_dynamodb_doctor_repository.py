"""Unit tests for the DynamoDB doctor repository adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_doctor_repository import (
    DynamoDBDoctorRepository,
)
from deskai.adapters.persistence.schema import DoctorProfileFields as F
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import PlanType


@patch("deskai.adapters.persistence.base_repository.boto3")
class DynamoDBDoctorRepositoryTest(unittest.TestCase):
    def _make_repo(self, mock_boto3: MagicMock) -> DynamoDBDoctorRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBDoctorRepository(table_name="deskai-doctors")

    # --- helpers ---

    def _canonical_item(self, **overrides: str) -> dict:
        """Build a DynamoDB item using canonical schema constants.

        Uses ``DoctorProfileFields.build_item`` so that any rename in
        the schema module is immediately reflected in the test fixtures
        — eliminating the circular validation problem.
        """
        defaults = dict(
            identity_provider_id="sub-abc-123",
            doctor_id="doc-001",
            email="ana@clinic.com",
            full_name="Dra. Ana",
            clinic_id="clinic-01",
            clinic_name="Clinica Vida",
            plan_type="plus",
            created_at="2025-01-15T10:00:00Z",
        )
        defaults.update(overrides)
        return F.build_item(**defaults)

    # --- find_by_identity_provider_id ---

    def test_find_by_identity_provider_id_found(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        item = self._canonical_item()
        self.mock_table.get_item.return_value = {"Item": item}

        result = repo.find_by_identity_provider_id("sub-abc-123")

        self.assertEqual(
            result,
            DoctorProfile(
                doctor_id="doc-001",
                identity_provider_id="sub-abc-123",
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

    def test_find_by_identity_provider_id_not_found(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {}

        result = repo.find_by_identity_provider_id("sub-missing")

        self.assertIsNone(result)

    def test_find_by_identity_provider_id_parses_all_fields(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        item = self._canonical_item(
            identity_provider_id="sub-xyz-999",
            doctor_id="doc-99",
            email="carlos@saude.com",
            full_name="Dr. Carlos",
            clinic_id="clinic-77",
            clinic_name="Centro Saude",
            plan_type="pro",
            created_at="2024-06-01T08:30:00Z",
        )
        self.mock_table.get_item.return_value = {"Item": item}

        result = repo.find_by_identity_provider_id("sub-xyz-999")

        self.assertIsNotNone(result)
        self.assertEqual(result.doctor_id, "doc-99")
        self.assertEqual(result.identity_provider_id, "sub-xyz-999")
        self.assertEqual(result.email, "carlos@saude.com")
        self.assertEqual(result.name, "Dr. Carlos")
        self.assertEqual(result.clinic_id, "clinic-77")
        self.assertEqual(result.clinic_name, "Centro Saude")
        self.assertEqual(result.plan_type, PlanType.PRO)
        self.assertEqual(result.created_at, "2024-06-01T08:30:00Z")

    def test_find_by_identity_provider_id_free_trial_plan(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        item = self._canonical_item(
            identity_provider_id="sub-trial",
            doctor_id="doc-ft",
            email="trial@clinic.com",
            full_name="Dr. Trial",
            clinic_id="clinic-ft",
            clinic_name="Free Clinic",
            plan_type="free_trial",
            created_at="2025-03-01T00:00:00Z",
        )
        self.mock_table.get_item.return_value = {"Item": item}

        result = repo.find_by_identity_provider_id("sub-trial")

        self.assertEqual(result.plan_type, PlanType.FREE_TRIAL)

    # --- Schema drift protection ---

    def test_reads_full_name_field_from_canonical_schema(self, mock_boto3: MagicMock) -> None:
        """Proves the repo reads the canonical ``full_name`` field."""
        repo = self._make_repo(mock_boto3)
        item = self._canonical_item(full_name="Dr. Canonical")
        # Remove legacy field to prove full_name is primary
        item.pop(F.LEGACY_NAME, None)
        self.mock_table.get_item.return_value = {"Item": item}

        result = repo.find_by_identity_provider_id("sub-abc-123")

        self.assertEqual(result.name, "Dr. Canonical")

    def test_falls_back_to_legacy_name_field(self, mock_boto3: MagicMock) -> None:
        """Proves backward compat with records that only have ``name``."""
        repo = self._make_repo(mock_boto3)
        item = self._canonical_item(full_name="Dr. Legacy")
        # Simulate old record: has ``name`` but no ``full_name``
        item.pop(F.FULL_NAME, None)
        item[F.LEGACY_NAME] = "Dr. Legacy"
        self.mock_table.get_item.return_value = {"Item": item}

        result = repo.find_by_identity_provider_id("sub-abc-123")

        self.assertEqual(result.name, "Dr. Legacy")

    def test_missing_clinic_name_raises_validation_error(self, mock_boto3: MagicMock) -> None:
        """Records without ``clinic_name`` cause a domain validation
        error because the entity requires it.  This test documents the
        behaviour so we catch data-seeding omissions early.
        """
        from deskai.shared.errors import DomainValidationError

        repo = self._make_repo(mock_boto3)
        item = self._canonical_item()
        item.pop(F.CLINIC_NAME, None)
        self.mock_table.get_item.return_value = {"Item": item}

        with self.assertRaises(DomainValidationError):
            repo.find_by_identity_provider_id("sub-abc-123")

    # --- count_consultations_this_month ---

    def test_count_consultations_this_month(self, mock_boto3: MagicMock) -> None:
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
            call_kwargs["ExpressionAttributeValues"][":sk_prefix"].startswith("CONSULTATION#")
        )

    def test_count_consultations_this_month_zero(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Count": 0}

        result = repo.count_consultations_this_month("doc-new")

        self.assertEqual(result, 0)

    def test_count_consultations_missing_count_key(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {}

        result = repo.count_consultations_this_month("doc-001")

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
