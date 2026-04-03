"""Consultation domain services — status transition logic."""

from dataclasses import replace

from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.consultation.exceptions import InvalidStatusTransitionError
from deskai.shared.time import utc_now_iso

ALLOWED_TRANSITIONS: dict[ConsultationStatus, set[ConsultationStatus]] = {
    ConsultationStatus.STARTED: {ConsultationStatus.RECORDING},
    ConsultationStatus.RECORDING: {ConsultationStatus.IN_PROCESSING},
    ConsultationStatus.IN_PROCESSING: {
        ConsultationStatus.DRAFT_GENERATED,
        ConsultationStatus.PROCESSING_FAILED,
    },
    ConsultationStatus.PROCESSING_FAILED: {ConsultationStatus.IN_PROCESSING},
    ConsultationStatus.DRAFT_GENERATED: {ConsultationStatus.UNDER_PHYSICIAN_REVIEW},
    ConsultationStatus.UNDER_PHYSICIAN_REVIEW: {
        ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
        ConsultationStatus.FINALIZED,
    },
    ConsultationStatus.FINALIZED: set(),
}


def validate_transition(
    from_status: ConsultationStatus, to_status: ConsultationStatus
) -> bool:
    """Check whether a status transition is allowed."""
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def transition_consultation(
    consultation: Consultation,
    new_status: ConsultationStatus,
    **kwargs: object,
) -> Consultation:
    """Apply a status transition, returning a new frozen Consultation instance."""
    if not validate_transition(consultation.status, new_status):
        raise InvalidStatusTransitionError(
            from_status=consultation.status.value,
            to_status=new_status.value,
        )
    return replace(consultation, status=new_status, updated_at=utc_now_iso(), **kwargs)
