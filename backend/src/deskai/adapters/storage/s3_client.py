"""Thin wrapper around boto3 S3 client for JSON and binary operations."""

import json

import boto3
from botocore.exceptions import ClientError

from deskai.shared.logging import get_logger

logger = get_logger()


class S3Client:
    """Low-level S3 operations scoped to a single bucket."""

    def __init__(self, bucket_name: str) -> None:
        self._bucket = bucket_name
        self._s3 = boto3.client("s3")

    def put_json(self, key: str, data: dict) -> None:
        """Serialize *data* as JSON and store it under *key*."""
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=json.dumps(data, ensure_ascii=False),
            ContentType="application/json",
        )

    def get_json(self, key: str) -> dict | None:
        """Return the deserialized JSON at *key*, or ``None`` if missing."""
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"].read()
            return json.loads(body)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        """Store raw *data* bytes under *key*."""
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* exists in the bucket."""
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise
