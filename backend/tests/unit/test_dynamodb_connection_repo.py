"""Unit tests for the DynamoDB connection repository adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.persistence.dynamodb_connection_repository import (
    DynamoDBConnectionRepository,
)
from deskai.domain.session.value_objects import ConnectionInfo


@patch("deskai.adapters.persistence.dynamodb_connection_repository.boto3")
class DynamoDBConnectionRepositoryTest(unittest.TestCase):
    def _make_repo(self, mock_boto3: MagicMock) -> DynamoDBConnectionRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBConnectionRepository(table_name="test-table")

    # ---- save + find ----

    def test_save_and_find_by_connection_id(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        connection = ConnectionInfo(
            connection_id="conn-001",
            session_id="sess-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            connected_at="2026-04-02T10:00:00+00:00",
        )

        repo.save(connection)

        call_kwargs = self.mock_table.put_item.call_args[1]
        item = call_kwargs["Item"]
        self.assertEqual(item["PK"], "CONNECTION#conn-001")
        self.assertEqual(item["SK"], "METADATA")
        self.assertEqual(item["connection_id"], "conn-001")
        self.assertEqual(item["session_id"], "sess-001")
        self.assertEqual(item["doctor_id"], "doc-001")
        self.assertEqual(item["clinic_id"], "clinic-001")
        self.assertEqual(item["connected_at"], "2026-04-02T10:00:00+00:00")

    def test_find_by_connection_id_returns_connection_when_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {
            "Item": {
                "PK": "CONNECTION#conn-001",
                "SK": "METADATA",
                "connection_id": "conn-001",
                "session_id": "sess-001",
                "doctor_id": "doc-001",
                "clinic_id": "clinic-001",
                "connected_at": "2026-04-02T10:00:00+00:00",
            }
        }

        result = repo.find_by_connection_id("conn-001")

        self.assertIsNotNone(result)
        self.assertEqual(result.connection_id, "conn-001")
        self.assertEqual(result.session_id, "sess-001")
        self.assertEqual(result.doctor_id, "doc-001")
        self.mock_table.get_item.assert_called_once_with(
            Key={"PK": "CONNECTION#conn-001", "SK": "METADATA"}
        )

    def test_find_by_connection_id_returns_none_when_not_found(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {}

        result = repo.find_by_connection_id("conn-missing")

        self.assertIsNone(result)

    # ---- remove ----

    def test_remove_deletes_item(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)

        repo.remove("conn-001")

        self.mock_table.delete_item.assert_called_once_with(
            Key={"PK": "CONNECTION#conn-001", "SK": "METADATA"}
        )


if __name__ == "__main__":
    unittest.main()
