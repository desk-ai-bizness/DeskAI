"""Review domain services — finalization guards and review validation."""

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.review.exceptions import (
    ExportNotAllowedError,
    FinalizationNotAllowedError,
    ReviewNotAvailableError,
    ReviewNotEditableError,
)

# Statuses that allow opening the review screen
_REVIEWABLE_STATUSES = frozenset(
    {
        ConsultationStatus.DRAFT_GENERATED,
        ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
        ConsultationStatus.FINALIZED,
    }
)

# Status required for editing
_EDITABLE_STATUS = ConsultationStatus.UNDER_PHYSICIAN_REVIEW

# Status required for finalization
_FINALIZABLE_STATUS = ConsultationStatus.UNDER_PHYSICIAN_REVIEW

# Status required for export
_EXPORTABLE_STATUS = ConsultationStatus.FINALIZED


def validate_review_access(consultation_id: str, status: ConsultationStatus) -> None:
    """Raise if the consultation is not in a reviewable state."""
    if status not in _REVIEWABLE_STATUSES:
        raise ReviewNotAvailableError(consultation_id, status.value)


def validate_review_editable(consultation_id: str, status: ConsultationStatus) -> None:
    """Raise if the consultation is not in an editable review state."""
    if status != _EDITABLE_STATUS:
        raise ReviewNotEditableError(consultation_id, status.value)


def validate_finalization(consultation_id: str, status: ConsultationStatus) -> None:
    """Raise if the consultation cannot be finalized."""
    if status == ConsultationStatus.FINALIZED:
        return  # Idempotent: already finalized is not an error
    if status != _FINALIZABLE_STATUS:
        raise FinalizationNotAllowedError(
            consultation_id,
            f"status must be '{_FINALIZABLE_STATUS.value}', got '{status.value}'",
        )


def validate_export(consultation_id: str, status: ConsultationStatus) -> None:
    """Raise if the consultation cannot be exported."""
    if status != _EXPORTABLE_STATUS:
        raise ExportNotAllowedError(consultation_id, status.value)


def is_already_finalized(status: ConsultationStatus) -> bool:
    """Check if consultation is already finalized (for idempotency)."""
    return status == ConsultationStatus.FINALIZED
