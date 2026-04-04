"""Integration test: consultation DynamoDB round-trip with moto."""

import unittest

import boto3
from moto import mock_aws

from deskai.adapters.persistence.dynamodb_consultation_repository import (
    DynamoDBConsultationRepository,
)
from deskai.domain.consultation.entities import Consultation, ConsultationStatus


@mock_aws
class TestConsultationRoundTrip(unittest.TestCase):
    """Verify save() -> find_by_id() produces identical entity."""

    def setUp(self):
        # Create real DynamoDB table
        self.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        self.table = self.dynamodb.create_table(
            TableName="test-table",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_doctor_date",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        self.repo = DynamoDBConsultationRepository(table_name="test-table")

    def test_save_and_find_by_id_round_trip(self):
        """Entity survives save -> DynamoDB -> find_by_id without data loss."""
        original = Consultation(
            consultation_id="cons-rt-001",
            clinic_id="clinic-rt-001",
            doctor_id="doc-rt-001",
            patient_id="pat-rt-001",
            specialty="cardiology",
            status=ConsultationStatus.STARTED,
            scheduled_date="2026-04-03",
            notes="Integration test notes",
            created_at="2026-04-03T10:00:00+00:00",
            updated_at="2026-04-03T10:00:00+00:00",
            session_started_at="2026-04-03T10:30:00+00:00",
        )

        self.repo.save(original)
        loaded = self.repo.find_by_id("cons-rt-001", "clinic-rt-001")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.consultation_id, original.consultation_id)
        self.assertEqual(loaded.clinic_id, original.clinic_id)
        self.assertEqual(loaded.doctor_id, original.doctor_id)
        self.assertEqual(loaded.patient_id, original.patient_id)
        self.assertEqual(loaded.specialty, original.specialty)
        self.assertEqual(loaded.status, original.status)
        self.assertEqual(loaded.scheduled_date, original.scheduled_date)
        self.assertEqual(loaded.notes, original.notes)
        self.assertEqual(loaded.created_at, original.created_at)
        self.assertEqual(loaded.updated_at, original.updated_at)
        self.assertEqual(loaded.session_started_at, original.session_started_at)
        # Optional fields that were None should stay None
        self.assertIsNone(loaded.session_ended_at)
        self.assertIsNone(loaded.processing_started_at)
        self.assertIsNone(loaded.error_details)

    def test_find_by_id_not_found(self):
        """find_by_id returns None for nonexistent item."""
        result = self.repo.find_by_id("nonexistent", "clinic-001")
        self.assertIsNone(result)

    def test_find_by_doctor_and_date_range(self):
        """GSI query returns correct consultations within date range."""
        c1 = Consultation(
            consultation_id="c1",
            clinic_id="cl1",
            doctor_id="doc1",
            patient_id="p1",
            specialty="gp",
            scheduled_date="2026-04-01",
            created_at="2026-04-01T10:00:00+00:00",
            updated_at="2026-04-01T10:00:00+00:00",
        )
        c2 = Consultation(
            consultation_id="c2",
            clinic_id="cl1",
            doctor_id="doc1",
            patient_id="p2",
            specialty="gp",
            scheduled_date="2026-04-05",
            created_at="2026-04-05T10:00:00+00:00",
            updated_at="2026-04-05T10:00:00+00:00",
        )
        self.repo.save(c1)
        self.repo.save(c2)

        results = self.repo.find_by_doctor_and_date_range(
            "doc1", "2026-04-01", "2026-04-03"
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].consultation_id, "c1")
