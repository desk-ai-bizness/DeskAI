"""Audit domain entities."""

from dataclasses import dataclass
from enum import StrEnum

from deskai.shared.errors import DomainValidationError


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

    def __post_init__(self) -> None:
        if not self.event_id or not self.event_id.strip():
            raise DomainValidationError("event_id must be a non-empty string")
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not isinstance(self.event_type, AuditAction):
            raise DomainValidationError(f"event_type must be an AuditAction, got {type(self.event_type).__name__}")
        if not self.actor_id or not self.actor_id.strip():
            raise DomainValidationError("actor_id must be a non-empty string")
        if not self.timestamp or not self.timestamp.strip():
            raise DomainValidationError("timestamp must be a non-empty string")
