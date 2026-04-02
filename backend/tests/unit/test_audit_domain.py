"""Unit tests for the audit domain."""

import unittest

from deskai.domain.audit.entities import AuditAction, AuditEvent


class AuditActionEnumTest(unittest.TestCase):
    def test_all_eleven_action_values_exist(self) -> None:
        expected = {
            "consultation.created",
            "session.started",
            "session.ended",
            "processing.started",
            "processing.completed",
            "processing.failed",
            "review.opened",
            "review.edited",
            "insight.actioned",
            "consultation.finalized",
            "export.generated",
        }
        actual = {a.value for a in AuditAction}
        self.assertEqual(actual, expected)

    def test_action_count(self) -> None:
        self.assertEqual(len(AuditAction), 11)


class AuditEventEntityTest(unittest.TestCase):
    def test_create_audit_event_with_all_fields(self) -> None:
        event = AuditEvent(
            event_id="evt-001",
            consultation_id="c-100",
            event_type=AuditAction.CONSULTATION_CREATED,
            actor_id="doc-1",
            timestamp="2026-04-01T10:00:00+00:00",
            payload={"specialty": "general_practice"},
        )
        self.assertEqual(event.event_id, "evt-001")
        self.assertEqual(event.consultation_id, "c-100")
        self.assertEqual(event.event_type, AuditAction.CONSULTATION_CREATED)
        self.assertEqual(event.actor_id, "doc-1")
        self.assertEqual(event.timestamp, "2026-04-01T10:00:00+00:00")
        self.assertEqual(event.payload, {"specialty": "general_practice"})

    def test_audit_event_with_none_payload(self) -> None:
        event = AuditEvent(
            event_id="evt-002",
            consultation_id="c-100",
            event_type=AuditAction.SESSION_STARTED,
            actor_id="doc-1",
            timestamp="2026-04-01T10:05:00+00:00",
        )
        self.assertIsNone(event.payload)

    def test_audit_event_is_frozen(self) -> None:
        event = AuditEvent(
            event_id="evt-003",
            consultation_id="c-100",
            event_type=AuditAction.SESSION_ENDED,
            actor_id="doc-1",
            timestamp="2026-04-01T10:30:00+00:00",
        )
        with self.assertRaises(AttributeError):
            event.actor_id = "doc-2"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
