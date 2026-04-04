"""Finalize a consultation — lock the record with physician confirmation."""

from dataclasses import dataclass, replace
from typing import Any

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.review.entities import FinalizedRecord
from deskai.domain.review.services import is_already_finalized, validate_finalization
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


@dataclass(frozen=True)
class FinalizeConsultationUseCase:
    """Lock the consultation, store final version, record audit event."""

    consultation_repo: ConsultationRepository
    artifact_repo: ArtifactRepository
    audit_repo: AuditRepository

    def execute(
        self,
        auth_context: AuthContext,
        consultation_id: str,
        clinic_id: str,
    ) -> Consultation:
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise ConsultationNotFoundError(f"Consultation {consultation_id} not found")
        if consultation.doctor_id != auth_context.doctor_id:
            raise ConsultationOwnershipError("Requesting doctor does not own this consultation")

        validate_finalization(consultation_id, consultation.status)

        # Idempotent: return existing finalized consultation
        if is_already_finalized(consultation.status):
            logger.info(
                "finalization_idempotent",
                extra=log_context(consultation_id=consultation_id),
            )
            return consultation

        now = utc_now_iso()

        # Load current artifacts (edited or original)
        medical_history = self._load_final_artifact(
            clinic_id,
            consultation_id,
            "medical_history",
            ArtifactType.MEDICAL_HISTORY,
        )
        summary = self._load_final_artifact(
            clinic_id,
            consultation_id,
            "summary",
            ArtifactType.SUMMARY,
        )
        insights_raw = self.artifact_repo.get_artifact(
            clinic_id, consultation_id, ArtifactType.INSIGHTS
        )
        accepted_insights = self._filter_accepted_insights(clinic_id, consultation_id, insights_raw)

        # Build and store final version
        final_record = FinalizedRecord(
            consultation_id=consultation_id,
            clinic_id=clinic_id,
            doctor_id=auth_context.doctor_id,
            patient_id=consultation.patient_id,
            medical_history=medical_history or {},
            summary=summary or {},
            accepted_insights=accepted_insights,
            finalized_at=now,
            finalized_by=auth_context.doctor_id,
        )

        self.artifact_repo.save_artifact(
            clinic_id,
            consultation_id,
            ArtifactType.FINAL_VERSION,
            {
                "consultation_id": final_record.consultation_id,
                "clinic_id": final_record.clinic_id,
                "doctor_id": final_record.doctor_id,
                "patient_id": final_record.patient_id,
                "medical_history": final_record.medical_history,
                "summary": final_record.summary,
                "accepted_insights": final_record.accepted_insights,
                "finalized_at": final_record.finalized_at,
                "finalized_by": final_record.finalized_by,
            },
        )

        # Transition consultation to finalized
        finalized = replace(
            consultation,
            status=ConsultationStatus.FINALIZED,
            finalized_at=now,
            finalized_by=auth_context.doctor_id,
            updated_at=now,
        )
        self.consultation_repo.save(finalized)

        # Audit event
        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.CONSULTATION_FINALIZED,
                actor_id=auth_context.doctor_id,
                timestamp=now,
            )
        )

        logger.info(
            "consultation_finalized",
            extra=log_context(
                consultation_id=consultation_id,
                doctor_id=auth_context.doctor_id,
            ),
        )

        return finalized

    def _load_final_artifact(
        self,
        clinic_id: str,
        consultation_id: str,
        edit_field: str,
        artifact_type: ArtifactType,
    ) -> dict[str, Any] | None:
        """Load the physician-edited version if it exists, else the AI original."""
        edits = self.artifact_repo.get_artifact(
            clinic_id, consultation_id, ArtifactType.PHYSICIAN_EDITS
        )
        if edits and edit_field in edits:
            return edits[edit_field]
        return self.artifact_repo.get_artifact(clinic_id, consultation_id, artifact_type)

    def _filter_accepted_insights(
        self,
        clinic_id: str,
        consultation_id: str,
        insights_raw: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Return only insights that were accepted by the physician."""
        if not insights_raw:
            return []

        all_insights = insights_raw.get("observacoes", [])
        edits = self.artifact_repo.get_artifact(
            clinic_id, consultation_id, ArtifactType.PHYSICIAN_EDITS
        )

        if not edits or "insight_actions" not in edits:
            return all_insights

        actions_by_id: dict[str, dict[str, Any]] = {}
        for action_item in edits["insight_actions"]:
            iid = action_item.get("insight_id", "")
            if iid:
                actions_by_id[iid] = action_item

        accepted = []
        for i, insight in enumerate(all_insights):
            insight_id = str(i)
            action_data = actions_by_id.get(insight_id, {})
            action = action_data.get("action", "pending")
            if action in ("accepted", "pending", "edited"):
                accepted.append(insight)

        return accepted
