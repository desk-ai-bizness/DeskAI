"""Stub adapter for EventPublisher -- raises NotImplementedError."""

from typing import Any

from deskai.ports.event_publisher import EventPublisher


class StubEventPublisher(EventPublisher):
    """Placeholder until a real event publisher is built."""

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError(
            "Not yet implemented: EventPublisher.publish"
        )

    def publish_batch(
        self, events: list[tuple[str, dict[str, Any]]]
    ) -> None:
        raise NotImplementedError(
            "Not yet implemented: EventPublisher.publish_batch"
        )
