"""EventBridge adapter for publishing domain events."""

import json
from typing import Any

import boto3

from deskai.ports.event_publisher import EventPublisher
from deskai.shared.logging import get_logger

logger = get_logger()

_SOURCE = "deskai.consultation"


class EventBridgePublisher(EventPublisher):
    """Publish domain events to an Amazon EventBridge bus."""

    def __init__(self, event_bus_name: str) -> None:
        self._bus_name = event_bus_name
        self._client = boto3.client("events")

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        response = self._client.put_events(Entries=[self._build_entry(event_type, payload)])
        failed = response.get("FailedEntryCount", 0)
        if failed:
            entry = response["Entries"][0]
            raise RuntimeError(
                f"Failed to publish event '{event_type}': "
                f"{entry.get('ErrorCode')} - {entry.get('ErrorMessage')}"
            )
        logger.info("event_published", extra={"event_type": event_type})

    def publish_batch(self, events: list[tuple[str, dict[str, Any]]]) -> None:
        entries = [self._build_entry(et, p) for et, p in events]
        response = self._client.put_events(Entries=entries)
        failed = response.get("FailedEntryCount", 0)
        if failed:
            raise RuntimeError(f"Failed to publish {failed}/{len(entries)} events")
        logger.info("events_published_batch", extra={"count": len(entries)})

    def _build_entry(self, event_type: str, payload: dict[str, Any]) -> dict:
        return {
            "Source": _SOURCE,
            "DetailType": event_type,
            "Detail": json.dumps(payload),
            "EventBusName": self._bus_name,
        }
