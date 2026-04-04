"""Contract tests for DynamoDB repositories.

These tests use HARDCODED raw dicts with literal string keys as DynamoDB
item fixtures.  They deliberately do NOT use ``build_item()`` or schema
constants (``F.*``).  This breaks the circular-validation pattern:

    Code reads:   item[F.FULL_NAME]   # F.FULL_NAME == "full_name"
    Test fixture: {"full_name": "Dr. Ana"}  # hardcoded, independent

If someone renames a constant in schema.py without updating the real
DynamoDB data, these contract tests will fail — exactly the bug class
that tautological tests miss.

Numeric fields use ``decimal.Decimal`` to match real boto3 DynamoDB
return types.
"""

import json
import unittest
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Doctor Profile contract
# ---------------------------------------------------------------------------


class TestDoctorProfileContract(unittest.TestCase):
    """DynamoDB item shape contract for DOCTOR#<id> / PROFILE."""

    def _make_repo(self, mock_boto3: MagicMock):
        from deskai.adapters.persistence.dynamodb_doctor_repository import (
            DynamoDBDoctorRepository,
        )

        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBDoctorRepository(table_name="test-table")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_from_hardcoded_dynamodb_item(self, mock_boto3):
        """Repository must correctly deserialize a real DynamoDB item shape."""
        repo = self._make_repo(mock_boto3)

        # Hardcoded item — mirrors what a Cognito post-confirmation Lambda
        # or seed script would actually write to DynamoDB.
        raw_item = {
            "PK": "DOCTOR#cognito-sub-abc",
            "SK": "PROFILE",
            "doctor_id": "doc-abc",
            "email": "ana@clinic.com",
            "full_name": "Dra. Ana Silva",
            "name": "Dra. Ana Silva",
            "clinic_id": "clinic-xyz",
            "clinic_name": "Clinica Central",
            "plan_type": "plus",
            "created_at": "2026-01-10T09:00:00+00:00",
            "updated_at": "2026-03-15T14:30:00+00:00",
            "cognito_sub": "cognito-sub-abc",
            "specialty": "cardiology",
        }

        self.mock_table.get_item.return_value = {"Item": raw_item}
        profile = repo.find_by_identity_provider_id("cognito-sub-abc")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.doctor_id, "doc-abc")
        self.assertEqual(profile.email, "ana@clinic.com")
        self.assertEqual(profile.name, "Dra. Ana Silva")
        self.assertEqual(profile.clinic_id, "clinic-xyz")
        self.assertEqual(profile.clinic_name, "Clinica Central")
        self.assertEqual(profile.plan_type.value, "plus")
        self.assertEqual(
            profile.created_at,
            datetime(2026, 1, 10, 9, 0, 0, tzinfo=UTC),
        )

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_legacy_name_fallback(self, mock_boto3):
        """If full_name is missing, repository falls back to legacy 'name' field."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "DOCTOR#cognito-sub-old",
            "SK": "PROFILE",
            "doctor_id": "doc-old",
            "email": "old@clinic.com",
            # "full_name" is deliberately missing (old record)
            "name": "Dr. Legacy Name",
            "clinic_id": "clinic-001",
            "clinic_name": "Old Clinic",
            "plan_type": "free_trial",
            "created_at": "2025-06-01T10:00:00+00:00",
        }

        self.mock_table.get_item.return_value = {"Item": raw_item}
        profile = repo.find_by_identity_provider_id("cognito-sub-old")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.name, "Dr. Legacy Name")


# ---------------------------------------------------------------------------
# Consultation contract
# ---------------------------------------------------------------------------


class TestConsultationContract(unittest.TestCase):
    """DynamoDB item shape contract for CLINIC#<id> / CONSULTATION#<id>."""

    def _make_repo(self, mock_boto3: MagicMock):
        from deskai.adapters.persistence.dynamodb_consultation_repository import (
            DynamoDBConsultationRepository,
        )

        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBConsultationRepository(table_name="test-table")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_from_hardcoded_dynamodb_item(self, mock_boto3):
        """Repository must correctly deserialize a real DynamoDB item shape."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "CLINIC#clinic-001",
            "SK": "CONSULTATION#cons-001",
            "GSI1PK": "DOCTOR#doc-001",
            "GSI1SK": "CONSULTATION#2026-04-01#cons-001",
            "consultation_id": "cons-001",
            "clinic_id": "clinic-001",
            "doctor_id": "doc-001",
            "patient_id": "pat-001",
            "specialty": "general_practice",
            "status": "started",
            "scheduled_date": "2026-04-01",
            "notes": "Patient complains of headache",
            "created_at": "2026-04-01T08:00:00+00:00",
            "updated_at": "2026-04-01T08:00:00+00:00",
            "session_started_at": "2026-04-01T08:15:00+00:00",
        }

        self.mock_table.get_item.return_value = {"Item": raw_item}
        c = repo.find_by_id("cons-001", "clinic-001")

        self.assertIsNotNone(c)
        self.assertEqual(c.consultation_id, "cons-001")
        self.assertEqual(c.clinic_id, "clinic-001")
        self.assertEqual(c.doctor_id, "doc-001")
        self.assertEqual(c.patient_id, "pat-001")
        self.assertEqual(c.specialty, "general_practice")
        self.assertEqual(c.status.value, "started")
        self.assertEqual(c.scheduled_date, "2026-04-01")
        self.assertEqual(c.notes, "Patient complains of headache")
        self.assertEqual(c.created_at, "2026-04-01T08:00:00+00:00")
        self.assertEqual(c.session_started_at, "2026-04-01T08:15:00+00:00")
        self.assertIsNone(c.session_ended_at)
        self.assertIsNone(c.processing_started_at)
        self.assertIsNone(c.finalized_at)
        self.assertIsNone(c.error_details)

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_save_produces_correct_key_schema(self, mock_boto3):
        """save() must produce PK/SK/GSI keys matching the documented schema."""
        from deskai.domain.consultation.entities import (
            Consultation,
            ConsultationStatus,
        )

        repo = self._make_repo(mock_boto3)
        consultation = Consultation(
            consultation_id="cons-002",
            clinic_id="clinic-002",
            doctor_id="doc-002",
            patient_id="pat-002",
            specialty="dermatology",
            status=ConsultationStatus.STARTED,
            scheduled_date="2026-04-03",
            notes="",
            created_at="2026-04-03T10:00:00+00:00",
            updated_at="2026-04-03T10:00:00+00:00",
        )
        repo.save(consultation)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]

        # Assert against hardcoded string keys — NOT F.* constants
        self.assertEqual(item["PK"], "CLINIC#clinic-002")
        self.assertEqual(item["SK"], "CONSULTATION#cons-002")
        self.assertEqual(item["GSI1PK"], "DOCTOR#doc-002")
        self.assertEqual(item["GSI1SK"], "CONSULTATION#2026-04-03#cons-002")
        self.assertEqual(item["consultation_id"], "cons-002")
        self.assertEqual(item["status"], "started")


# ---------------------------------------------------------------------------
# Session contract
# ---------------------------------------------------------------------------


class TestSessionContract(unittest.TestCase):
    """DynamoDB item shape contract for SESSION#<id> / METADATA."""

    def _make_repo(self, mock_boto3: MagicMock):
        from deskai.adapters.persistence.dynamodb_session_repository import (
            DynamoDBSessionRepository,
        )

        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBSessionRepository(table_name="test-table")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_from_hardcoded_dynamodb_item_with_decimal(self, mock_boto3):
        """Repository handles boto3 Decimal types for numeric fields."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "SESSION#sess-001",
            "SK": "METADATA",
            "GSI1PK": "CONSULTATION#cons-001",
            "GSI1SK": "SESSION#sess-001",
            "session_id": "sess-001",
            "consultation_id": "cons-001",
            "doctor_id": "doc-001",
            "clinic_id": "clinic-001",
            "state": "recording",
            "started_at": "2026-04-01T10:00:00+00:00",
            # boto3 returns numbers as Decimal, not int
            "duration_seconds": Decimal("600"),
            "audio_chunks_received": Decimal("42"),
            "connection_id": "conn-abc",
        }

        self.mock_table.get_item.return_value = {"Item": raw_item}
        s = repo.find_by_id("sess-001")

        self.assertIsNotNone(s)
        self.assertEqual(s.session_id, "sess-001")
        self.assertEqual(s.consultation_id, "cons-001")
        self.assertEqual(s.doctor_id, "doc-001")
        self.assertEqual(s.clinic_id, "clinic-001")
        self.assertEqual(s.state.value, "recording")
        self.assertEqual(s.started_at, "2026-04-01T10:00:00+00:00")
        # Numeric fields must survive Decimal -> int conversion
        self.assertEqual(s.duration_seconds, 600)
        self.assertIsInstance(s.duration_seconds, int)
        self.assertEqual(s.audio_chunks_received, 42)
        self.assertIsInstance(s.audio_chunks_received, int)
        self.assertEqual(s.connection_id, "conn-abc")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_with_all_optional_fields_missing(self, mock_boto3):
        """Repository handles items where all optional fields are absent."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "SESSION#sess-min",
            "SK": "METADATA",
            "session_id": "sess-min",
            "consultation_id": "cons-min",
            "doctor_id": "doc-min",
            "clinic_id": "clinic-min",
            "state": "connecting",
            "started_at": "2026-04-01T10:00:00+00:00",
            "duration_seconds": Decimal("0"),
            "audio_chunks_received": Decimal("0"),
            # No connection_id, ended_at, grace_period_expires_at, last_activity_at
        }

        self.mock_table.get_item.return_value = {"Item": raw_item}
        s = repo.find_by_id("sess-min")

        self.assertIsNotNone(s)
        self.assertIsNone(s.connection_id)
        self.assertIsNone(s.ended_at)
        self.assertIsNone(s.grace_period_expires_at)
        self.assertIsNone(s.last_activity_at)
        self.assertEqual(s.duration_seconds, 0)
        self.assertEqual(s.audio_chunks_received, 0)

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_save_produces_correct_key_schema(self, mock_boto3):
        """save() must produce PK/SK/GSI keys matching the documented schema."""
        from deskai.domain.session.entities import Session, SessionState

        repo = self._make_repo(mock_boto3)
        session = Session(
            session_id="sess-002",
            consultation_id="cons-002",
            doctor_id="doc-002",
            clinic_id="clinic-002",
            state=SessionState.ACTIVE,
            started_at="2026-04-03T10:00:00+00:00",
        )
        repo.save(session)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]

        self.assertEqual(item["PK"], "SESSION#sess-002")
        self.assertEqual(item["SK"], "METADATA")
        self.assertEqual(item["GSI1PK"], "CONSULTATION#cons-002")
        self.assertEqual(item["GSI1SK"], "SESSION#sess-002")
        self.assertEqual(item["session_id"], "sess-002")
        self.assertEqual(item["state"], "active")


# ---------------------------------------------------------------------------
# Patient contract
# ---------------------------------------------------------------------------


class TestPatientContract(unittest.TestCase):
    """DynamoDB item shape contract for CLINIC#<id> / PATIENT#<id>."""

    def _make_repo(self, mock_boto3: MagicMock):
        from deskai.adapters.persistence.dynamodb_patient_repository import (
            DynamoDBPatientRepository,
        )

        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBPatientRepository(table_name="test-table")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_from_hardcoded_dynamodb_item(self, mock_boto3):
        """Repository must correctly deserialize a real DynamoDB item shape."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "CLINIC#clinic-001",
            "SK": "PATIENT#pat-001",
            "patient_id": "pat-001",
            "name": "Maria Santos",
            "date_of_birth": "1985-03-22",
            "clinic_id": "clinic-001",
            "created_at": "2026-01-15T09:00:00+00:00",
        }

        self.mock_table.get_item.return_value = {"Item": raw_item}
        p = repo.find_by_id("pat-001", "clinic-001")

        self.assertIsNotNone(p)
        self.assertEqual(p.patient_id, "pat-001")
        self.assertEqual(p.name, "Maria Santos")
        self.assertEqual(p.date_of_birth, "1985-03-22")
        self.assertEqual(p.clinic_id, "clinic-001")
        self.assertEqual(p.created_at, "2026-01-15T09:00:00+00:00")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_save_produces_correct_key_schema(self, mock_boto3):
        """save() must produce PK/SK matching the documented schema."""
        from deskai.domain.patient.entities import Patient

        repo = self._make_repo(mock_boto3)
        patient = Patient(
            patient_id="pat-002",
            name="Carlos Oliveira",
            date_of_birth="1990-07-10",
            clinic_id="clinic-002",
            created_at="2026-04-01T10:00:00+00:00",
        )
        repo.save(patient)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]

        self.assertEqual(item["PK"], "CLINIC#clinic-002")
        self.assertEqual(item["SK"], "PATIENT#pat-002")
        self.assertEqual(item["patient_id"], "pat-002")
        self.assertEqual(item["name"], "Carlos Oliveira")


# ---------------------------------------------------------------------------
# Audit contract
# ---------------------------------------------------------------------------


class TestAuditContract(unittest.TestCase):
    """DynamoDB item shape contract for CONSULTATION#<id> / AUDIT#<ts>#<id>."""

    def _make_repo(self, mock_boto3: MagicMock):
        from deskai.adapters.persistence.dynamodb_audit_repository import (
            DynamoDBAuditRepository,
        )

        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBAuditRepository(table_name="test-table")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_from_hardcoded_dynamodb_item(self, mock_boto3):
        """Repository must correctly deserialize a real DynamoDB item shape."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "CONSULTATION#cons-001",
            "SK": "AUDIT#2026-04-01T10:00:00+00:00#evt-001",
            "event_id": "evt-001",
            "consultation_id": "cons-001",
            "event_type": "consultation.created",
            "actor_id": "doc-001",
            "timestamp": "2026-04-01T10:00:00+00:00",
            "payload": json.dumps({"source": "api"}),
        }

        self.mock_table.query.return_value = {"Items": [raw_item]}
        events = repo.find_by_consultation("cons-001")

        self.assertEqual(len(events), 1)
        e = events[0]
        self.assertEqual(e.event_id, "evt-001")
        self.assertEqual(e.consultation_id, "cons-001")
        self.assertEqual(e.event_type.value, "consultation.created")
        self.assertEqual(e.actor_id, "doc-001")
        self.assertEqual(e.timestamp, "2026-04-01T10:00:00+00:00")
        self.assertEqual(e.payload, {"source": "api"})

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_with_null_payload(self, mock_boto3):
        """Repository handles items where payload is absent."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "CONSULTATION#cons-002",
            "SK": "AUDIT#2026-04-02T10:00:00+00:00#evt-002",
            "event_id": "evt-002",
            "consultation_id": "cons-002",
            "event_type": "session.started",
            "actor_id": "doc-002",
            "timestamp": "2026-04-02T10:00:00+00:00",
            # No "payload" key
        }

        self.mock_table.query.return_value = {"Items": [raw_item]}
        events = repo.find_by_consultation("cons-002")

        self.assertEqual(len(events), 1)
        self.assertIsNone(events[0].payload)

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_append_produces_correct_key_schema(self, mock_boto3):
        """append() must produce PK/SK matching the documented schema."""
        from deskai.domain.audit.entities import AuditAction, AuditEvent

        repo = self._make_repo(mock_boto3)
        event = AuditEvent(
            event_id="evt-003",
            consultation_id="cons-003",
            event_type=AuditAction.CONSULTATION_CREATED,
            actor_id="doc-003",
            timestamp="2026-04-03T10:00:00+00:00",
            payload={"key": "value"},
        )
        repo.append(event)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]

        self.assertEqual(item["PK"], "CONSULTATION#cons-003")
        self.assertEqual(item["SK"], "AUDIT#2026-04-03T10:00:00+00:00#evt-003")
        self.assertEqual(item["event_id"], "evt-003")
        self.assertEqual(item["event_type"], "consultation.created")
        self.assertEqual(item["payload"], '{"key": "value"}')


# ---------------------------------------------------------------------------
# Connection contract
# ---------------------------------------------------------------------------


class TestConnectionContract(unittest.TestCase):
    """DynamoDB item shape contract for CONNECTION#<id> / METADATA."""

    def _make_repo(self, mock_boto3: MagicMock):
        from deskai.adapters.persistence.dynamodb_connection_repository import (
            DynamoDBConnectionRepository,
        )

        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBConnectionRepository(table_name="test-table")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_deserializes_from_hardcoded_dynamodb_item(self, mock_boto3):
        """Repository must correctly deserialize a real DynamoDB item shape."""
        repo = self._make_repo(mock_boto3)

        raw_item = {
            "PK": "CONNECTION#conn-abc123",
            "SK": "METADATA",
            "connection_id": "conn-abc123",
            "session_id": "sess-001",
            "doctor_id": "doc-001",
            "clinic_id": "clinic-001",
            "connected_at": "2026-04-01T10:00:00+00:00",
        }

        self.mock_table.get_item.return_value = {"Item": raw_item}
        conn = repo.find_by_connection_id("conn-abc123")

        self.assertIsNotNone(conn)
        self.assertEqual(conn.connection_id, "conn-abc123")
        self.assertEqual(conn.session_id, "sess-001")
        self.assertEqual(conn.doctor_id, "doc-001")
        self.assertEqual(conn.clinic_id, "clinic-001")
        self.assertEqual(conn.connected_at, "2026-04-01T10:00:00+00:00")

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_save_produces_correct_key_schema(self, mock_boto3):
        """save() must produce PK/SK matching the documented schema."""
        from deskai.domain.session.value_objects import ConnectionInfo

        repo = self._make_repo(mock_boto3)
        conn = ConnectionInfo(
            connection_id="conn-xyz",
            session_id="sess-002",
            doctor_id="doc-002",
            clinic_id="clinic-002",
            connected_at="2026-04-03T11:00:00+00:00",
        )
        repo.save(conn)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]

        self.assertEqual(item["PK"], "CONNECTION#conn-xyz")
        self.assertEqual(item["SK"], "METADATA")
        self.assertEqual(item["connection_id"], "conn-xyz")
        self.assertEqual(item["session_id"], "sess-002")


if __name__ == "__main__":
    unittest.main()
