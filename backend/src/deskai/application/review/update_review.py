"""Apply physician edits to a consultation under review."""

from dataclasses import dataclass
from typing import Any

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.review.services import validate_review_editable
from deskai.domain.review.value_objects import ReviewUpdate
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


@dataclass(frozen=True)
class UpdateReviewUseCase:
    """Persist physician edits and record audit events."""

    consultation_repo: ConsultationRepository
    artifact_repo: ArtifactRepository
    audit_repo: AuditRepository

    def execute(
        self,
        auth_context: AuthContext,
        consultation_id: str,
        clinic_id: str,
        update: ReviewUpdate,
    ) -> dict[str, Any]:
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise ConsultationNotFoundError(f"Consultation {consultation_id} not found")
        if consultation.doctor_id != auth_context.doctor_id:
            raise ConsultationOwnershipError("Requesting doctor does not own this consultation")

        validate_review_editable(consultation_id, consultation.status)

        now = utc_now_iso()

        # Load existing edits or start fresh
        existing_edits = (
            self.artifact_repo.get_artifact(
                clinic_id, consultation_id, ArtifactType.PHYSICIAN_EDITS
            )
            or {}
        )

        # Apply new edits
        if update.medical_history is not None:
            existing_edits["medical_history"] = update.medical_history
        if update.summary is not None:
            existing_edits["summary"] = update.summary
        if update.insight_actions is not None:
            existing_edits["insight_actions"] = update.insight_actions

        existing_edits["last_edited_at"] = now
        existing_edits["last_edited_by"] = auth_context.doctor_id

        # Persist edits
        self.artifact_repo.save_artifact(
            clinic_id,
            consultation_id,
            ArtifactType.PHYSICIAN_EDITS,
            existing_edits,
        )

        # Audit events per edited field
        for field_name in update.edited_fields():
            self.audit_repo.append(
                AuditEvent(
                    event_id=new_uuid(),
                    consultation_id=consultation_id,
                    event_type=AuditAction.REVIEW_EDITED,
                    actor_id=auth_context.doctor_id,
                    timestamp=now,
                    payload={"edited_field": field_name},
                )
            )

        # Audit events per insight action
        if update.insight_actions:
            for action_item in update.insight_actions:
                insight_id = action_item.get("insight_id", "")
                action = action_item.get("action", "")
                if insight_id and action:
                    self.audit_repo.append(
                        AuditEvent(
                            event_id=new_uuid(),
                            consultation_id=consultation_id,
                            event_type=AuditAction.INSIGHT_ACTIONED,
                            actor_id=auth_context.doctor_id,
                            timestamp=now,
                            payload={
                                "insight_id": insight_id,
                                "action": action,
                            },
                        )
                    )

        logger.info(
            "review_updated",
            extra=log_context(
                consultation_id=consultation_id,
                doctor_id=auth_context.doctor_id,
                edited_fields=update.edited_fields(),
            ),
        )

        return existing_edits
