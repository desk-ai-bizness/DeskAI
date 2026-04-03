"""Port interface for domain event publishing."""

from abc import ABC, abstractmethod


class EventPublisher(ABC):
    """Contract for publishing domain events to an external bus."""

    @abstractmethod
    def publish(
        self,
        event_type: str,
        payload: dict,
    ) -> None:
        """Publish a domain event with the given type and payload."""
