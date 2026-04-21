"""Review domain entities."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.shared.errors import DomainValidationError


class InsightAction(StrEnum):
    """Actions a physician can take on an insight."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    EDITED = "edited"


@dataclass(frozen=True)
class InsightReviewItem:
    """Tracks physician action on a single insight."""

    insight_id: str
    action: InsightAction = InsightAction.PENDING
    physician_note: str = ""

    def __post_init__(self) -> None:
        if not self.insight_id or not self.insight_id.strip():
            raise DomainValidationError("insight_id must be a non-empty string")
        if not isinstance(self.action, InsightAction):
            raise DomainValidationError(
                f"action must be an InsightAction, got {type(self.action).__name__}"
            )


@dataclass(frozen=True)
class ReviewPayload:
    """Aggregated review data for a consultation."""

    consultation_id: str
    status: ConsultationStatus = ConsultationStatus.UNDER_PHYSICIAN_REVIEW
    medical_history: dict[str, Any] | None = None
    summary: dict[str, Any] | None = None
    insights: list[dict[str, Any]] | None = None
    transcript_segments: list[dict[str, Any]] | None = None
    medical_history_edited: bool = False
    summary_edited: bool = False
    insight_actions: list[InsightReviewItem] = field(default_factory=list)
    completeness_warning: bool = False

    def __post_init__(self) -> None:
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not isinstance(self.status, ConsultationStatus):
            raise DomainValidationError("status must be a ConsultationStatus")


@dataclass(frozen=True)
class FinalizedRecord:
    """Immutable final version of a consultation record."""

    consultation_id: str
    clinic_id: str
    doctor_id: str
    patient_id: str
    medical_history: dict[str, Any]
    summary: dict[str, Any]
    accepted_insights: list[dict[str, Any]]
    finalized_at: str
    finalized_by: str

    def __post_init__(self) -> None:
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")
        if not self.doctor_id or not self.doctor_id.strip():
            raise DomainValidationError("doctor_id must be a non-empty string")
        if not self.finalized_at or not self.finalized_at.strip():
            raise DomainValidationError("finalized_at must be a non-empty string")
        if not self.finalized_by or not self.finalized_by.strip():
            raise DomainValidationError("finalized_by must be a non-empty string")
