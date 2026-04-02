"""Audit domain entities."""

from dataclasses import dataclass
from enum import StrEnum


class AuditAction(StrEnum):
    """Actions tracked in the audit trail."""

    CONSULTATION_CREATED = "consultation.created"
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    PROCESSING_STARTED = "processing.started"
    PROCESSING_COMPLETED = "processing.completed"
    PROCESSING_FAILED = "processing.failed"
    REVIEW_OPENED = "review.opened"
    REVIEW_EDITED = "review.edited"
    INSIGHT_ACTIONED = "insight.actioned"
    CONSULTATION_FINALIZED = "consultation.finalized"
    EXPORT_GENERATED = "export.generated"


@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit trail entry."""

    event_id: str
    consultation_id: str
    event_type: AuditAction
    actor_id: str
    timestamp: str
    payload: dict[str, object] | None = None
