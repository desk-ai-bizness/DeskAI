"""Thin wrapper around boto3 S3 client for JSON and binary operations."""

import json

import boto3
from botocore.exceptions import ClientError

from deskai.shared.logging import get_logger, log_context

logger = get_logger()
_SSE_MODE = "aws:kms"


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
            ServerSideEncryption=_SSE_MODE,
        )
        logger.debug("s3_put_json", extra=log_context(bucket=self._bucket, key=key))

    def get_json(self, key: str) -> dict | None:
        """Return the deserialized JSON at *key*, or ``None`` if missing."""
        try:
            response = self._s3.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"].read()
            logger.debug("s3_get_json", extra=log_context(bucket=self._bucket, key=key, found=True))
            return json.loads(body)
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                logger.debug(
                    "s3_get_json",
                    extra=log_context(bucket=self._bucket, key=key, found=False),
                )
                return None
            raise

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        """Store raw *data* bytes under *key*."""
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            ServerSideEncryption=_SSE_MODE,
        )
        logger.debug(
            "s3_put_bytes",
            extra=log_context(
                bucket=self._bucket,
                key=key,
                content_type=content_type,
                size_bytes=len(data),
            ),
        )

    def exists(self, key: str) -> bool:
        """Return ``True`` if *key* exists in the bucket."""
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            result = True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                result = False
            else:
                raise
        logger.debug(
            "s3_exists_check",
            extra=log_context(bucket=self._bucket, key=key, exists=result),
        )
        return result

    def generate_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        """Generate a time-limited download URL for the given key."""
        url = self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
        logger.debug(
            "s3_presigned_url",
            extra=log_context(
                bucket=self._bucket,
                key=key,
                expires_in=expires_in_seconds,
            ),
        )
        return url
