"""Stub adapter for EventPublisher."""

from deskai.ports.event_publisher import EventPublisher


class StubEventPublisher(EventPublisher):
    def publish(self, event_type: str, payload: dict) -> None:
        raise NotImplementedError("Not yet implemented: EventPublisher.publish")
