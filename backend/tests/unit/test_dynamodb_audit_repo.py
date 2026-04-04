"""Unit tests for the DynamoDB audit repository adapter."""

import json
import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_audit_repository import (
    DynamoDBAuditRepository,
)
from deskai.domain.audit.entities import AuditAction, AuditEvent


@patch("deskai.adapters.persistence.base_repository.boto3")
class DynamoDBAuditRepositoryTest(unittest.TestCase):
    def _make_repo(
        self, mock_boto3: MagicMock
    ) -> DynamoDBAuditRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBAuditRepository(table_name="test-table")

    # ---- append ----

    def test_append_puts_item_with_correct_pk_sk(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        event = AuditEvent(
            event_id="evt-001",
            consultation_id="cons-001",
            event_type=AuditAction.CONSULTATION_CREATED,
            actor_id="doc-01",
            timestamp="2026-04-02T10:00:00Z",
        )

        repo.append(event)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["PK"], "CONSULTATION#cons-001")
        self.assertEqual(
            item["SK"], "AUDIT#2026-04-02T10:00:00Z#evt-001"
        )

    def test_append_stores_all_event_fields(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        payload = {"old_status": "started", "new_status": "recording"}
        event = AuditEvent(
            event_id="evt-002",
            consultation_id="cons-001",
            event_type=AuditAction.SESSION_STARTED,
            actor_id="doc-01",
            timestamp="2026-04-02T10:05:00Z",
            payload=payload,
        )

        repo.append(event)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["event_id"], "evt-002")
        self.assertEqual(item["consultation_id"], "cons-001")
        self.assertEqual(
            item["event_type"], "session.started"
        )
        self.assertEqual(item["actor_id"], "doc-01")
        self.assertEqual(item["timestamp"], "2026-04-02T10:05:00Z")
        self.assertEqual(
            json.loads(item["payload"]),
            {"old_status": "started", "new_status": "recording"},
        )

    def test_append_includes_condition_expression_to_prevent_overwrite(
        self, mock_boto3: MagicMock
    ) -> None:
        """Append must include ConditionExpression for append-only enforcement."""
        repo = self._make_repo(mock_boto3)
        event = AuditEvent(
            event_id="evt-001",
            consultation_id="cons-001",
            event_type=AuditAction.CONSULTATION_CREATED,
            actor_id="doc-01",
            timestamp="2026-04-02T10:00:00Z",
        )

        repo.append(event)

        call_kwargs = self.mock_table.put_item.call_args[1]
        self.assertEqual(
            call_kwargs["ConditionExpression"],
            "attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )

    def test_append_duplicate_raises_conflict_error(
        self, mock_boto3: MagicMock
    ) -> None:
        """Appending the same event twice must fail (append-only enforcement)."""
        from botocore.exceptions import ClientError

        from deskai.shared.errors import ConflictError

        repo = self._make_repo(mock_boto3)
        self.mock_table.put_item.side_effect = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "exists"}},
            "PutItem",
        )
        event = AuditEvent(
            event_id="evt-001",
            consultation_id="cons-001",
            event_type=AuditAction.CONSULTATION_CREATED,
            actor_id="doc-01",
            timestamp="2026-04-02T10:00:00Z",
        )

        with self.assertRaises(ConflictError):
            repo.append(event)

    # ---- find_by_consultation ----

    def test_find_by_consultation_queries_with_begins_with(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}

        repo.find_by_consultation("cons-001")

        call_kwargs = self.mock_table.query.call_args[1]
        self.assertIn("CONSULTATION#cons-001", str(call_kwargs))

    def test_find_by_consultation_returns_sorted_events(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "event_id": "evt-001",
                    "consultation_id": "cons-001",
                    "event_type": "consultation.created",
                    "actor_id": "doc-01",
                    "timestamp": "2026-04-02T10:00:00Z",
                },
                {
                    "event_id": "evt-002",
                    "consultation_id": "cons-001",
                    "event_type": "session.started",
                    "actor_id": "doc-01",
                    "timestamp": "2026-04-02T10:05:00Z",
                    "payload": json.dumps({"key": "value"}),
                },
            ]
        }

        result = repo.find_by_consultation("cons-001")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].event_id, "evt-001")
        self.assertEqual(
            result[0].event_type, AuditAction.CONSULTATION_CREATED
        )
        self.assertIsNone(result[0].payload)
        self.assertEqual(result[1].event_id, "evt-002")
        self.assertEqual(
            result[1].event_type, AuditAction.SESSION_STARTED
        )
        self.assertEqual(result[1].payload, {"key": "value"})

    def test_find_by_consultation_returns_empty_list(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}

        result = repo.find_by_consultation("cons-none")

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
