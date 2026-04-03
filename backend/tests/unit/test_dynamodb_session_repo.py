"""Unit tests for the DynamoDB session repository adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_session_repository import (
    DynamoDBSessionRepository,
)
from deskai.domain.session.entities import Session, SessionState


@patch("deskai.adapters.persistence.base_repository.boto3")
class DynamoDBSessionRepositoryTest(unittest.TestCase):
    def _make_repo(self, mock_boto3: MagicMock) -> DynamoDBSessionRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBSessionRepository(table_name="test-table")

    def _make_session(self, **overrides: object) -> Session:
        defaults = dict(
            session_id="sess-001",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ACTIVE,
            started_at="2026-04-02T10:00:00+00:00",
        )
        defaults.update(overrides)
        return Session(**defaults)

    # ---- save ----

    def test_save_puts_item_with_correct_keys(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        session = self._make_session()

        repo.save(session)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["PK"], "SESSION#sess-001")
        self.assertEqual(item["SK"], "METADATA")
        self.assertEqual(item["consultation_id"], "cons-001")
        self.assertEqual(item["doctor_id"], "doc-001")
        self.assertEqual(item["clinic_id"], "clinic-001")
        self.assertEqual(item["state"], "active")
        self.assertEqual(item["started_at"], "2026-04-02T10:00:00+00:00")

    def test_save_includes_gsi_for_consultation_lookup(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        session = self._make_session()

        repo.save(session)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["GSI1PK"], "CONSULTATION#cons-001")
        self.assertEqual(item["GSI1SK"], "SESSION#sess-001")

    # ---- find_by_id ----

    def test_find_by_id_returns_session_when_found(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {
            "Item": {
                "PK": "SESSION#sess-001",
                "SK": "METADATA",
                "GSI1PK": "CONSULTATION#cons-001",
                "GSI1SK": "SESSION#sess-001",
                "session_id": "sess-001",
                "consultation_id": "cons-001",
                "doctor_id": "doc-001",
                "clinic_id": "clinic-001",
                "state": "active",
                "started_at": "2026-04-02T10:00:00+00:00",
                "audio_chunks_received": 5,
            }
        }

        result = repo.find_by_id("sess-001")

        self.assertIsNotNone(result)
        self.assertEqual(result.session_id, "sess-001")
        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.state, SessionState.ACTIVE)
        self.assertEqual(result.audio_chunks_received, 5)
        self.mock_table.get_item.assert_called_once_with(
            Key={"PK": "SESSION#sess-001", "SK": "METADATA"}
        )

    def test_find_by_id_returns_none_when_not_found(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {}

        result = repo.find_by_id("sess-missing")

        self.assertIsNone(result)

    # ---- find_active_by_consultation_id ----

    def test_find_active_by_consultation_id_returns_session(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "session_id": "sess-001",
                    "consultation_id": "cons-001",
                    "doctor_id": "doc-001",
                    "clinic_id": "clinic-001",
                    "state": "active",
                    "started_at": "2026-04-02T10:00:00+00:00",
                    "audio_chunks_received": 0,
                }
            ]
        }

        result = repo.find_active_by_consultation_id("cons-001")

        self.assertIsNotNone(result)
        self.assertEqual(result.session_id, "sess-001")
        self.assertEqual(result.state, SessionState.ACTIVE)
        call_kwargs = self.mock_table.query.call_args[1]
        self.assertEqual(call_kwargs["IndexName"], "consultation-session-index")

    def test_find_active_by_consultation_id_returns_none_when_not_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}

        result = repo.find_active_by_consultation_id("cons-missing")

        self.assertIsNone(result)

    # ---- update ----

    def test_update_puts_item(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        session = self._make_session(state=SessionState.ENDED, ended_at="2026-04-02T11:00:00+00:00")

        repo.update(session)

        self.mock_table.put_item.assert_called_once()
        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["state"], "ended")
        self.assertEqual(item["ended_at"], "2026-04-02T11:00:00+00:00")

    # ---- delete ----

    def test_delete_removes_item(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)

        repo.delete("sess-001")

        self.mock_table.delete_item.assert_called_once_with(
            Key={"PK": "SESSION#sess-001", "SK": "METADATA"}
        )


if __name__ == "__main__":
    unittest.main()
