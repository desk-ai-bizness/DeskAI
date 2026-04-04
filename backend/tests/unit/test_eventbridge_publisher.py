"""Unit tests for the EventBridge event publisher adapter."""

import json
import unittest
from unittest.mock import MagicMock, patch


class EventBridgePublisherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock()
        self.mock_client.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{}]}

        with patch("boto3.client", return_value=self.mock_client):
            from deskai.adapters.events.eventbridge_publisher import (
                EventBridgePublisher,
            )

            self.publisher = EventBridgePublisher(event_bus_name="deskai-dev-event-bus")

    def test_publish_sends_correct_event(self) -> None:
        self.publisher.publish(
            "consultation.session.ended",
            {"consultation_id": "cons-001", "clinic_id": "clinic-001"},
        )

        self.mock_client.put_events.assert_called_once()
        call_args = self.mock_client.put_events.call_args
        entries = call_args[1]["Entries"] if "Entries" in call_args[1] else call_args[0][0]
        entry = entries[0]
        self.assertEqual(entry["Source"], "deskai.consultation")
        self.assertEqual(entry["DetailType"], "consultation.session.ended")
        self.assertEqual(entry["EventBusName"], "deskai-dev-event-bus")
        detail = json.loads(entry["Detail"])
        self.assertEqual(detail["consultation_id"], "cons-001")
        self.assertEqual(detail["clinic_id"], "clinic-001")

    def test_publish_batch_sends_multiple_entries(self) -> None:
        events = [
            ("consultation.session.ended", {"consultation_id": "cons-001", "clinic_id": "c1"}),
            ("consultation.session.ended", {"consultation_id": "cons-002", "clinic_id": "c2"}),
        ]

        self.publisher.publish_batch(events)

        self.mock_client.put_events.assert_called_once()
        call_args = self.mock_client.put_events.call_args
        entries = call_args[1]["Entries"] if "Entries" in call_args[1] else call_args[0][0]
        self.assertEqual(len(entries), 2)
        self.assertEqual(json.loads(entries[0]["Detail"])["consultation_id"], "cons-001")
        self.assertEqual(json.loads(entries[1]["Detail"])["consultation_id"], "cons-002")

    def test_publish_raises_on_failed_entries(self) -> None:
        self.mock_client.put_events.return_value = {
            "FailedEntryCount": 1,
            "Entries": [{"ErrorCode": "InternalFailure", "ErrorMessage": "boom"}],
        }

        with self.assertRaises(RuntimeError) as ctx:
            self.publisher.publish(
                "consultation.session.ended",
                {"consultation_id": "cons-001", "clinic_id": "clinic-001"},
            )

        self.assertIn("Failed to publish", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
