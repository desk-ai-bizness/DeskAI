"""Unit tests for the S3Client wrapper."""

import json
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from deskai.adapters.storage.s3_client import S3Client


class S3ClientTest(unittest.TestCase):
    """Tests for S3Client with mocked boto3."""

    def setUp(self) -> None:
        self.mock_s3 = MagicMock(name="s3-client")
        patcher = patch("deskai.adapters.storage.s3_client.boto3")
        self.mock_boto3 = patcher.start()
        self.mock_boto3.client.return_value = self.mock_s3
        self.addCleanup(patcher.stop)
        self.client = S3Client(bucket_name="test-bucket")

    # ---- put_json ----

    def test_put_json_calls_put_object_with_serialized_body(self) -> None:
        data = {"key": "value", "count": 42}

        self.client.put_json("some/key.json", data)

        self.mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="some/key.json",
            Body=json.dumps(data, ensure_ascii=False),
            ContentType="application/json",
            ServerSideEncryption="aws:kms",
        )

    def test_put_json_handles_unicode(self) -> None:
        data = {"nome": "Joao da Silva"}

        self.client.put_json("path/data.json", data)

        call_kwargs = self.mock_s3.put_object.call_args[1]
        body = call_kwargs["Body"]
        self.assertIn("Joao da Silva", body)

    def test_put_json_propagates_client_error(self) -> None:
        self.mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "forbidden"}},
            "PutObject",
        )

        with self.assertRaises(ClientError):
            self.client.put_json("key", {"a": 1})

    # ---- get_json ----

    def test_get_json_returns_deserialized_data(self) -> None:
        payload = {"result": "ok"}
        body_mock = MagicMock()
        body_mock.read.return_value = json.dumps(payload).encode("utf-8")
        self.mock_s3.get_object.return_value = {"Body": body_mock}

        result = self.client.get_json("some/key.json")

        self.assertEqual(result, payload)
        self.mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="some/key.json",
        )

    def test_get_json_returns_none_when_not_found(self) -> None:
        self.mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
            "GetObject",
        )

        result = self.client.get_json("missing/key.json")

        self.assertIsNone(result)

    def test_get_json_propagates_non_404_error(self) -> None:
        self.mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "forbidden"}},
            "GetObject",
        )

        with self.assertRaises(ClientError):
            self.client.get_json("some/key.json")

    # ---- put_bytes ----

    def test_put_bytes_calls_put_object_with_raw_body(self) -> None:
        data = b"raw audio bytes"

        self.client.put_bytes("audio/chunk.webm", data, "audio/webm")

        self.mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="audio/chunk.webm",
            Body=data,
            ContentType="audio/webm",
            ServerSideEncryption="aws:kms",
        )

    def test_put_bytes_propagates_client_error(self) -> None:
        self.mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "oops"}},
            "PutObject",
        )

        with self.assertRaises(ClientError):
            self.client.put_bytes("k", b"data", "application/octet-stream")

    # ---- exists ----

    def test_exists_returns_true_when_object_present(self) -> None:
        self.mock_s3.head_object.return_value = {"ContentLength": 100}

        self.assertTrue(self.client.exists("some/key.json"))
        self.mock_s3.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="some/key.json",
        )

    def test_exists_returns_false_when_not_found(self) -> None:
        self.mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "not found"}},
            "HeadObject",
        )

        self.assertFalse(self.client.exists("missing/key.json"))

    def test_exists_propagates_non_404_error(self) -> None:
        self.mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "403", "Message": "forbidden"}},
            "HeadObject",
        )

        with self.assertRaises(ClientError):
            self.client.exists("some/key.json")


if __name__ == "__main__":
    unittest.main()
