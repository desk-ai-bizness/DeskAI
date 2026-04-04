"""S3 adapter implementing the StorageProvider port."""

from deskai.adapters.storage.s3_client import S3Client
from deskai.ports.storage_provider import StorageProvider


class S3StorageProvider(StorageProvider):
    """Store and retrieve binary objects in S3."""

    def __init__(self, s3_client: S3Client) -> None:
        self._s3 = s3_client

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._s3.put_bytes(key, data, content_type)

    def get(self, key: str) -> bytes | None:
        raise NotImplementedError("Binary get not needed for MVP export flow")

    def exists(self, key: str) -> bool:
        return self._s3.exists(key)

    def delete(self, key: str) -> None:
        raise NotImplementedError("Delete not needed for MVP export flow")

    def generate_presigned_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        return self._s3.generate_presigned_url(key, expires_in_seconds)
