"""Port interface for domain event publishing."""

from abc import ABC, abstractmethod
from typing import Any


class EventPublisher(ABC):
    """Contract for publishing domain events to an event bus."""

    @abstractmethod
    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish a single domain event."""

    @abstractmethod
    def publish_batch(
        self, events: list[tuple[str, dict[str, Any]]]
    ) -> None:
        """Publish a batch of domain events atomically."""
