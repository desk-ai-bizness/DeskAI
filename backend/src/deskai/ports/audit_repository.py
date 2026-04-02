"""Port interface for audit trail persistence."""

from abc import ABC, abstractmethod

from deskai.domain.audit.entities import AuditEvent


class AuditRepository(ABC):
    """Abstract audit event repository."""

    @abstractmethod
    def append(self, event: AuditEvent) -> None:
        """Append an audit event to the trail."""

    @abstractmethod
    def find_by_consultation(self, consultation_id: str) -> list[AuditEvent]:
        """Retrieve all audit events for a consultation."""
