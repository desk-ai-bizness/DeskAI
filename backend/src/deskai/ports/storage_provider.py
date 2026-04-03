"""Port interface for binary object storage."""

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Contract for storing and retrieving binary objects."""

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store a binary blob at the given key."""

    @abstractmethod
    def get(self, key: str) -> bytes | None:
        """Retrieve a binary blob, or None if the key does not exist."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check whether a key exists in storage."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a binary blob from storage."""

    @abstractmethod
    def generate_presigned_url(
        self, key: str, expires_in_seconds: int = 3600
    ) -> str:
        """Generate a time-limited URL for direct client download."""
