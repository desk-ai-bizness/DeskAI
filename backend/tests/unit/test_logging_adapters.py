"""Tests for adapter logging behavior.

Verifies that DynamoDB base repository and S3 client emit structured
logs at the correct levels for operations and error scenarios.
"""

import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError, EndpointConnectionError, ReadTimeoutError

from deskai.shared.errors import ConnectionError, RepositoryError, ThrottleError


def _make_client_error(code: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": f"mock {code}"}},
        "TestOp",
    )


class DynamoDBBaseRepositoryLoggingTest(unittest.TestCase):
    """Verify DynamoDB base repository error-path logging."""

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def _make_repo(self, mock_boto3: MagicMock):
        from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository

        self.mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = self.mock_table
        mock_boto3.resource.return_value = mock_resource
        return DynamoDBBaseRepository(table_name="test-table")

    @patch("deskai.adapters.persistence.base_repository.logger")
    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_throttle_retry_logged_at_warning(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository

        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        repo = DynamoDBBaseRepository(table_name="test")

        # Throttle on first two attempts, succeed on third
        mock_table.get_item.side_effect = [
            _make_client_error("ProvisionedThroughputExceededException"),
            {"Item": {"PK": "test"}},
        ]

        with patch("deskai.adapters.persistence.base_repository.time"):
            repo._safe_get_item(Key={"PK": "test"})

        warning_events = [c.args[0] for c in mock_logger.warning.call_args_list]
        self.assertIn("dynamodb_throttle_retry", warning_events)

    @patch("deskai.adapters.persistence.base_repository.logger")
    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_throttle_retry_contains_attempt_info(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository

        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        repo = DynamoDBBaseRepository(table_name="test")

        mock_table.put_item.side_effect = [
            _make_client_error("ThrottlingException"),
            {},
        ]

        with patch("deskai.adapters.persistence.base_repository.time"):
            repo._safe_put_item(Item={"PK": "x"})

        retry_call = next(
            c for c in mock_logger.warning.call_args_list
            if c.args[0] == "dynamodb_throttle_retry"
        )
        extra = retry_call.kwargs.get("extra", {})
        self.assertEqual(extra["operation"], "put_item")
        self.assertEqual(extra["attempt"], 1)
        self.assertIn("delay_seconds", extra)

    @patch("deskai.adapters.persistence.base_repository.logger")
    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_client_error_logged_at_error(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository

        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        repo = DynamoDBBaseRepository(table_name="test")

        mock_table.query.side_effect = _make_client_error("InternalServerError")

        with self.assertRaises(RepositoryError):
            repo._safe_query(KeyConditionExpression="PK = :pk")

        error_call = next(
            c for c in mock_logger.error.call_args_list
            if c.args[0] == "dynamodb_client_error"
        )
        extra = error_call.kwargs.get("extra", {})
        self.assertEqual(extra["operation"], "query")
        self.assertEqual(extra["error_code"], "InternalServerError")

    @patch("deskai.adapters.persistence.base_repository.logger")
    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_connection_error_logged_at_error(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository

        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        repo = DynamoDBBaseRepository(table_name="test")

        mock_table.get_item.side_effect = EndpointConnectionError(endpoint_url="http://x")

        with self.assertRaises(ConnectionError):
            repo._safe_get_item(Key={"PK": "test"})

        error_events = [c.args[0] for c in mock_logger.error.call_args_list]
        self.assertIn("dynamodb_connection_error", error_events)

    @patch("deskai.adapters.persistence.base_repository.logger")
    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_timeout_logged_at_error(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository

        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        repo = DynamoDBBaseRepository(table_name="test")

        mock_table.get_item.side_effect = ReadTimeoutError(endpoint_url="http://x")

        with self.assertRaises(ConnectionError):
            repo._safe_get_item(Key={"PK": "test"})

        error_events = [c.args[0] for c in mock_logger.error.call_args_list]
        self.assertIn("dynamodb_timeout", error_events)

    @patch("deskai.adapters.persistence.base_repository.logger")
    @patch("deskai.adapters.persistence.base_repository.boto3")
    def test_throttle_exhausted_logged_at_error(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository

        mock_table = MagicMock()
        mock_resource = MagicMock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        repo = DynamoDBBaseRepository(table_name="test")

        mock_table.get_item.side_effect = _make_client_error("RequestLimitExceeded")

        with patch("deskai.adapters.persistence.base_repository.time"):
            with self.assertRaises(ThrottleError):
                repo._safe_get_item(Key={"PK": "test"})

        error_events = [c.args[0] for c in mock_logger.error.call_args_list]
        self.assertIn("dynamodb_throttle_exhausted", error_events)

        exhausted_call = next(
            c for c in mock_logger.error.call_args_list
            if c.args[0] == "dynamodb_throttle_exhausted"
        )
        extra = exhausted_call.kwargs.get("extra", {})
        self.assertEqual(extra["operation"], "get_item")
        self.assertEqual(extra["retries"], 3)


class S3ClientLoggingTest(unittest.TestCase):
    """Verify S3Client emits structured logs for operations."""

    @patch("deskai.adapters.storage.s3_client.logger")
    @patch("deskai.adapters.storage.s3_client.boto3")
    def test_put_json_logged_at_debug(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.storage.s3_client import S3Client

        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        client = S3Client(bucket_name="test-bucket")

        client.put_json("artifacts/test.json", {"key": "value"})

        debug_events = [c.args[0] for c in mock_logger.debug.call_args_list]
        self.assertIn("s3_put_json", debug_events)

    @patch("deskai.adapters.storage.s3_client.logger")
    @patch("deskai.adapters.storage.s3_client.boto3")
    def test_get_json_logged_with_found_flag(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.storage.s3_client import S3Client

        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        # Simulate object exists
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=b'{"data": 1}')),
        }
        client = S3Client(bucket_name="test-bucket")

        client.get_json("artifacts/test.json")

        get_call = next(
            c for c in mock_logger.debug.call_args_list
            if c.args[0] == "s3_get_json"
        )
        extra = get_call.kwargs.get("extra", {})
        self.assertIs(extra["found"], True)

    @patch("deskai.adapters.storage.s3_client.logger")
    @patch("deskai.adapters.storage.s3_client.boto3")
    def test_get_json_not_found_logged_with_found_false(
        self, mock_boto3: MagicMock, mock_logger: MagicMock,
    ) -> None:
        from deskai.adapters.storage.s3_client import S3Client

        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
            "GetObject",
        )
        client = S3Client(bucket_name="test-bucket")

        result = client.get_json("missing.json")

        self.assertIsNone(result)
        get_call = next(
            c for c in mock_logger.debug.call_args_list
            if c.args[0] == "s3_get_json"
        )
        extra = get_call.kwargs.get("extra", {})
        self.assertIs(extra["found"], False)


if __name__ == "__main__":
    unittest.main()
