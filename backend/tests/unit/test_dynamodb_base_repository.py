"""Unit tests for the DynamoDB base repository."""

import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError

from deskai.adapters.persistence.base_repository import (
    _BASE_BACKOFF_SECONDS,
    _MAX_RETRIES,
    DynamoDBBaseRepository,
)
from deskai.shared.errors import (
    ConflictError,
    ConnectionError,
    RepositoryError,
    ThrottleError,
)


def _make_client_error(code: str, message: str = "err") -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": message}},
        "TestOperation",
    )


@patch("deskai.adapters.persistence.base_repository.boto3")
class TestDynamoDBBaseRepository(unittest.TestCase):
    """Tests for safe wrappers and error mapping."""

    def _make_repo(self, mock_boto3: MagicMock) -> DynamoDBBaseRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBBaseRepository(table_name="test-table")

    # -- safe wrappers delegate correctly --------------------------------

    def test_safe_put_item_delegates(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        repo._safe_put_item(Item={"PK": "x"})
        self.mock_table.put_item.assert_called_once_with(Item={"PK": "x"})

    def test_safe_get_item_delegates(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.return_value = {"Item": {"PK": "x"}}
        result = repo._safe_get_item(Key={"PK": "x"})
        self.assertEqual(result, {"Item": {"PK": "x"}})

    def test_safe_delete_item_delegates(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        repo._safe_delete_item(Key={"PK": "x"})
        self.mock_table.delete_item.assert_called_once()

    def test_safe_update_item_delegates(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        repo._safe_update_item(
            Key={"PK": "x"},
            UpdateExpression="SET #a = :v",
            ExpressionAttributeNames={"#a": "attr"},
            ExpressionAttributeValues={":v": 1},
        )
        self.mock_table.update_item.assert_called_once()

    def test_safe_query_delegates(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}
        result = repo._safe_query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": "TEST#1"},
        )
        self.assertEqual(result, {"Items": []})

    # -- error mapping ---------------------------------------------------

    def test_conditional_check_raises_conflict(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.put_item.side_effect = _make_client_error(
            "ConditionalCheckFailedException"
        )
        with self.assertRaises(ConflictError):
            repo._safe_put_item(Item={"PK": "x"})

    def test_validation_exception_raises_repository_error(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.put_item.side_effect = _make_client_error(
            "ValidationException", "Bad input"
        )
        with self.assertRaises(RepositoryError):
            repo._safe_put_item(Item={"PK": "x"})

    def test_unknown_client_error_raises_repository_error(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.side_effect = _make_client_error(
            "InternalServerError"
        )
        with self.assertRaises(RepositoryError):
            repo._safe_query(KeyConditionExpression="PK = :pk")

    def test_endpoint_connection_error_raises_connection_error(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.side_effect = EndpointConnectionError(
            endpoint_url="http://localhost"
        )
        with self.assertRaises(ConnectionError):
            repo._safe_get_item(Key={"PK": "x"})

    def test_read_timeout_raises_connection_error(
        self, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.get_item.side_effect = ReadTimeoutError(
            endpoint_url="http://localhost"
        )
        with self.assertRaises(ConnectionError):
            repo._safe_get_item(Key={"PK": "x"})

    # -- throttle retry behaviour ----------------------------------------

    @patch("deskai.adapters.persistence.base_repository.time.sleep")
    def test_throttle_retries_with_backoff(
        self, mock_sleep: MagicMock, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        throttle = _make_client_error("ProvisionedThroughputExceededException")
        self.mock_table.put_item.side_effect = [
            throttle,
            throttle,
            {"ResponseMetadata": {"HTTPStatusCode": 200}},
        ]
        repo._safe_put_item(Item={"PK": "x"})

        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_any_call(_BASE_BACKOFF_SECONDS * 1)
        mock_sleep.assert_any_call(_BASE_BACKOFF_SECONDS * 2)

    @patch("deskai.adapters.persistence.base_repository.time.sleep")
    def test_throttle_exhausts_retries_raises_throttle_error(
        self, mock_sleep: MagicMock, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        throttle = _make_client_error("ThrottlingException")
        self.mock_table.put_item.side_effect = [throttle] * _MAX_RETRIES

        with self.assertRaises(ThrottleError):
            repo._safe_put_item(Item={"PK": "x"})

        self.assertEqual(mock_sleep.call_count, _MAX_RETRIES)

    @patch("deskai.adapters.persistence.base_repository.time.sleep")
    def test_request_limit_exceeded_retries(
        self, mock_sleep: MagicMock, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        throttle = _make_client_error("RequestLimitExceeded")
        self.mock_table.query.side_effect = [
            throttle,
            {"Items": [{"PK": "x"}]},
        ]
        result = repo._safe_query(KeyConditionExpression="PK = :pk")
        self.assertEqual(result, {"Items": [{"PK": "x"}]})
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("deskai.adapters.persistence.base_repository.time.sleep")
    def test_exponential_backoff_values(
        self, mock_sleep: MagicMock, mock_boto3: MagicMock
    ) -> None:
        repo = self._make_repo(mock_boto3)
        throttle = _make_client_error("ThrottlingException")
        self.mock_table.put_item.side_effect = [throttle] * _MAX_RETRIES

        with self.assertRaises(ThrottleError):
            repo._safe_put_item(Item={"PK": "x"})

        expected_delays = [
            _BASE_BACKOFF_SECONDS * (2 ** i) for i in range(_MAX_RETRIES)
        ]
        actual_delays = [c.args[0] for c in mock_sleep.call_args_list]
        self.assertEqual(actual_delays, expected_delays)


@patch("deskai.adapters.persistence.base_repository.boto3")
class TestPaginatedQuery(unittest.TestCase):
    """Tests for _paginated_query auto-pagination."""

    def _make_repo(self, mock_boto3: MagicMock) -> DynamoDBBaseRepository:
        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBBaseRepository(table_name="test-table")

    def test_single_page(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {
            "Items": [{"id": "1"}, {"id": "2"}],
        }
        result = repo._paginated_query(KeyConditionExpression="PK = :pk")
        self.assertEqual(result, [{"id": "1"}, {"id": "2"}])
        self.assertEqual(self.mock_table.query.call_count, 1)

    def test_multiple_pages(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.side_effect = [
            {"Items": [{"id": "1"}], "LastEvaluatedKey": {"PK": "cursor"}},
            {"Items": [{"id": "2"}]},
        ]
        result = repo._paginated_query(KeyConditionExpression="PK = :pk")
        self.assertEqual(result, [{"id": "1"}, {"id": "2"}])
        self.assertEqual(self.mock_table.query.call_count, 2)

        second_call_kwargs = self.mock_table.query.call_args_list[1][1]
        self.assertEqual(
            second_call_kwargs["ExclusiveStartKey"], {"PK": "cursor"}
        )

    def test_empty_result(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.return_value = {"Items": []}
        result = repo._paginated_query(KeyConditionExpression="PK = :pk")
        self.assertEqual(result, [])

    def test_three_pages(self, mock_boto3: MagicMock) -> None:
        repo = self._make_repo(mock_boto3)
        self.mock_table.query.side_effect = [
            {"Items": [{"id": "1"}], "LastEvaluatedKey": {"PK": "c1"}},
            {"Items": [{"id": "2"}], "LastEvaluatedKey": {"PK": "c2"}},
            {"Items": [{"id": "3"}]},
        ]
        result = repo._paginated_query(KeyConditionExpression="PK = :pk")
        self.assertEqual(len(result), 3)
        self.assertEqual(self.mock_table.query.call_count, 3)


class TestConditionExpressionHelper(unittest.TestCase):
    """Tests for the _build_condition_expression static helper."""

    def test_builds_correct_structure(self) -> None:
        result = DynamoDBBaseRepository._build_condition_expression(
            "version", 5
        )
        self.assertEqual(
            result["ConditionExpression"], "#cond_attr = :cond_val"
        )
        self.assertEqual(
            result["ExpressionAttributeNames"], {"#cond_attr": "version"}
        )
        self.assertEqual(
            result["ExpressionAttributeValues"], {":cond_val": 5}
        )

    def test_with_string_value(self) -> None:
        result = DynamoDBBaseRepository._build_condition_expression(
            "status", "active"
        )
        self.assertEqual(
            result["ExpressionAttributeValues"], {":cond_val": "active"}
        )


@patch("deskai.adapters.persistence.base_repository.boto3")
class TestInitialization(unittest.TestCase):
    """Tests for constructor behaviour."""

    def test_stores_table_name(self, mock_boto3: MagicMock) -> None:
        mock_resource = MagicMock()
        mock_boto3.resource.return_value = mock_resource
        repo = DynamoDBBaseRepository(table_name="my-table")
        self.assertEqual(repo._table_name, "my-table")
        mock_resource.Table.assert_called_once_with("my-table")

    def test_creates_dynamodb_resource(self, mock_boto3: MagicMock) -> None:
        mock_resource = MagicMock()
        mock_boto3.resource.return_value = mock_resource
        DynamoDBBaseRepository(table_name="t")
        mock_boto3.resource.assert_called_once_with("dynamodb")


if __name__ == "__main__":
    unittest.main()
