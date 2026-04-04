"""Open the review screen for a consultation."""

from dataclasses import dataclass, replace
from typing import Any

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.review.entities import ReviewPayload
from deskai.domain.review.services import validate_review_access
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


@dataclass(frozen=True)
class OpenReviewUseCase:
    """Load consultation artifacts and transition to under_physician_review."""

    consultation_repo: ConsultationRepository
    artifact_repo: ArtifactRepository
    audit_repo: AuditRepository

    def execute(
        self,
        auth_context: AuthContext,
        consultation_id: str,
        clinic_id: str,
    ) -> ReviewPayload:
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise ConsultationNotFoundError(f"Consultation {consultation_id} not found")
        if consultation.doctor_id != auth_context.doctor_id:
            raise ConsultationOwnershipError("Requesting doctor does not own this consultation")

        validate_review_access(consultation_id, consultation.status)

        # Transition draft_generated -> under_physician_review on first access
        if consultation.status == ConsultationStatus.DRAFT_GENERATED:
            now = utc_now_iso()
            updated = replace(
                consultation,
                status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
                review_opened_at=now,
                updated_at=now,
            )
            self.consultation_repo.save(updated)

            self.audit_repo.append(
                AuditEvent(
                    event_id=new_uuid(),
                    consultation_id=consultation_id,
                    event_type=AuditAction.REVIEW_OPENED,
                    actor_id=auth_context.doctor_id,
                    timestamp=now,
                )
            )

            logger.info(
                "review_opened",
                extra=log_context(
                    consultation_id=consultation_id,
                    doctor_id=auth_context.doctor_id,
                ),
            )

        # Load artifacts
        medical_history = self.artifact_repo.get_artifact(
            clinic_id, consultation_id, ArtifactType.MEDICAL_HISTORY
        )
        summary = self.artifact_repo.get_artifact(clinic_id, consultation_id, ArtifactType.SUMMARY)
        insights = self.artifact_repo.get_artifact(
            clinic_id, consultation_id, ArtifactType.INSIGHTS
        )

        # Load physician edits if they exist
        edits = self.artifact_repo.get_artifact(
            clinic_id, consultation_id, ArtifactType.PHYSICIAN_EDITS
        )

        edited_history: dict[str, Any] | None = None
        edited_summary: dict[str, Any] | None = None
        history_edited = False
        summary_edited = False

        if edits:
            if "medical_history" in edits:
                edited_history = edits["medical_history"]
                history_edited = True
            if "summary" in edits:
                edited_summary = edits["summary"]
                summary_edited = True

        return ReviewPayload(
            consultation_id=consultation_id,
            medical_history=edited_history or medical_history,
            summary=edited_summary or summary,
            insights=insights.get("observacoes", []) if insights else [],
            medical_history_edited=history_edited,
            summary_edited=summary_edited,
        )
