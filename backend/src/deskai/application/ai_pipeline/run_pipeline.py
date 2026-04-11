"""Run the AI pipeline -- generate anamnesis, summary, and insights."""

import json
import logging
import time
from dataclasses import dataclass, replace

from deskai.domain.ai_pipeline.entities import PipelineResult, PipelineStatus
from deskai.domain.ai_pipeline.exceptions import (
    GenerationError,
    PipelineStepError,
    SchemaValidationError,
)
from deskai.domain.ai_pipeline.services import ArtifactValidator, EvidenceLinker
from deskai.domain.ai_pipeline.value_objects import (
    ArtifactResult,
    GenerationMetadata,
)
from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.llm_provider import LLMProvider
from deskai.ports.patient_repository import PatientRepository
from deskai.ports.transcript_repository import TranscriptRepository
from deskai.prompts import (
    ANAMNESIS_SYSTEM_PROMPT,
    ANAMNESIS_USER_TEMPLATE,
    INSIGHTS_SYSTEM_PROMPT,
    INSIGHTS_USER_TEMPLATE,
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_TEMPLATE,
)
from deskai.prompts.injection_defense import enforce_role_separation
from deskai.prompts.prompt_loader import render_prompt
from deskai.shared.identifiers import new_uuid
from deskai.shared.time import utc_now_iso

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunPipelineUseCase:
    """Orchestrate the 3-step AI pipeline for a consultation."""

    llm_provider: LLMProvider
    artifact_repo: ArtifactRepository
    consultation_repo: ConsultationRepository
    transcript_repo: TranscriptRepository
    patient_repo: PatientRepository
    audit_repo: AuditRepository
    transcript_lookup_attempts: int = 20
    transcript_lookup_interval_seconds: float = 3.0

    def execute(self, consultation_id: str, clinic_id: str) -> PipelineResult:
        started_at = utc_now_iso()

        # 1. Load consultation -- must be IN_PROCESSING
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise PipelineStepError("Consultation not found", "prerequisites", "not_found")
        if consultation.status != ConsultationStatus.IN_PROCESSING:
            raise PipelineStepError(
                f"Expected IN_PROCESSING, got {consultation.status}",
                "prerequisites",
                "invalid_status",
            )

        # 2. Load normalized transcript
        normalized = self._load_normalized_transcript_with_retry(
            clinic_id=clinic_id, consultation_id=consultation_id
        )
        if normalized is None:
            self._mark_failed(consultation, "Transcript not found")
            raise PipelineStepError(
                "Transcript not found",
                "prerequisites",
                "transcript_missing",
            )

        transcript_text = normalized.transcript_text

        # 3. Load patient
        patient = self.patient_repo.find_by_id(consultation.patient_id, clinic_id)
        patient_name = patient.name if patient else "nao_informado"
        patient_dob = patient.date_of_birth if patient else "nao_informado"
        consultation_date = consultation.scheduled_date or consultation.created_at[:10]

        # Audit: processing started
        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.PROCESSING_STARTED,
                actor_id="system",
                timestamp=started_at,
            )
        )

        # 4. Step 1 -- Anamnesis
        anamnesis_payload = None
        try:
            anamnesis_payload = self._generate_anamnesis(
                transcript_text,
                patient_name,
                patient_dob,
                consultation_date,
            )
            self.artifact_repo.save_artifact(
                clinic_id,
                consultation_id,
                ArtifactType.MEDICAL_HISTORY,
                anamnesis_payload,
            )
        except (GenerationError, SchemaValidationError) as exc:
            self._mark_failed(consultation, f"Anamnesis failed: {exc}")
            self._audit_failed(consultation_id, started_at, "anamnesis", str(exc))
            return PipelineResult(
                consultation_id=consultation_id,
                clinic_id=clinic_id,
                status=PipelineStatus.FAILED,
                started_at=started_at,
                completed_at=utc_now_iso(),
                error_message=f"Anamnesis failed: {exc}",
            )

        # 5. Step 2 -- Summary
        summary_payload = None
        try:
            summary_payload = self._generate_summary(
                transcript_text,
                json.dumps(anamnesis_payload, ensure_ascii=False),
                patient_name,
                patient_dob,
                consultation_date,
                consultation.specialty,
            )
            self.artifact_repo.save_artifact(
                clinic_id,
                consultation_id,
                ArtifactType.SUMMARY,
                summary_payload,
            )
        except (GenerationError, SchemaValidationError) as exc:
            self._update_status(consultation, ConsultationStatus.DRAFT_GENERATED)
            self._audit_completed(consultation_id, started_at, partial=True)
            meta = self._make_metadata(is_complete=True)
            return PipelineResult(
                consultation_id=consultation_id,
                clinic_id=clinic_id,
                status=PipelineStatus.PARTIALLY_COMPLETED,
                medical_history=ArtifactResult(
                    ArtifactType.MEDICAL_HISTORY,
                    anamnesis_payload,
                    meta,
                ),
                started_at=started_at,
                completed_at=utc_now_iso(),
                error_message=f"Summary failed: {exc}",
            )

        # 6. Step 3 -- Insights
        insights_payload = None
        try:
            insights_payload = self._generate_insights(
                transcript_text,
                json.dumps(anamnesis_payload, ensure_ascii=False),
                json.dumps(summary_payload, ensure_ascii=False),
                patient_name,
                patient_dob,
                consultation_date,
            )
            self.artifact_repo.save_artifact(
                clinic_id,
                consultation_id,
                ArtifactType.INSIGHTS,
                insights_payload,
            )
        except (GenerationError, SchemaValidationError):
            pass  # Fall through to partial completion below

        # 7. Update status and audit
        self._update_status(consultation, ConsultationStatus.DRAFT_GENERATED)

        meta = self._make_metadata(is_complete=True)
        completed_at = utc_now_iso()

        if insights_payload is not None:
            self._audit_completed(consultation_id, started_at, partial=False)
            return PipelineResult(
                consultation_id=consultation_id,
                clinic_id=clinic_id,
                status=PipelineStatus.COMPLETED,
                medical_history=ArtifactResult(
                    ArtifactType.MEDICAL_HISTORY,
                    anamnesis_payload,
                    meta,
                ),
                summary=ArtifactResult(ArtifactType.SUMMARY, summary_payload, meta),
                insights=ArtifactResult(ArtifactType.INSIGHTS, insights_payload, meta),
                started_at=started_at,
                completed_at=completed_at,
            )

        self._audit_completed(consultation_id, started_at, partial=True)
        return PipelineResult(
            consultation_id=consultation_id,
            clinic_id=clinic_id,
            status=PipelineStatus.PARTIALLY_COMPLETED,
            medical_history=ArtifactResult(
                ArtifactType.MEDICAL_HISTORY,
                anamnesis_payload,
                meta,
            ),
            summary=ArtifactResult(ArtifactType.SUMMARY, summary_payload, meta),
            started_at=started_at,
            completed_at=completed_at,
            error_message="Insights generation failed",
        )

    def _load_normalized_transcript_with_retry(
        self, clinic_id: str, consultation_id: str
    ):
        attempts = max(1, self.transcript_lookup_attempts)
        interval = max(0.0, self.transcript_lookup_interval_seconds)

        for attempt in range(1, attempts + 1):
            normalized = self.transcript_repo.get_normalized_transcript(
                clinic_id, consultation_id
            )
            if normalized is not None:
                if attempt > 1:
                    logger.info(
                        "transcript_found_after_retry",
                        extra={
                            "consultation_id": consultation_id,
                            "attempt": attempt,
                        },
                    )
                return normalized

            if attempt < attempts:
                logger.info(
                    "transcript_not_available_yet",
                    extra={
                        "consultation_id": consultation_id,
                        "attempt": attempt,
                        "max_attempts": attempts,
                    },
                )
                time.sleep(interval)

        return None

    # --- Private methods ---

    def _generate_anamnesis(
        self,
        transcript: str,
        patient_name: str,
        patient_dob: str,
        consultation_date: str,
    ) -> dict:
        user_msg = render_prompt(
            ANAMNESIS_USER_TEMPLATE,
            {
                "transcript": transcript,
                "patient_name": patient_name,
                "patient_dob": patient_dob,
                "consultation_date": consultation_date,
            },
        )
        system_prompt, user_content = enforce_role_separation(ANAMNESIS_SYSTEM_PROMPT, user_msg)
        result = self.llm_provider.generate_structured_output(
            "anamnesis",
            {
                "system_prompt": system_prompt,
                "user_message": user_content,
            },
        )
        missing = ArtifactValidator.validate_anamnesis(result.payload)
        if missing:
            raise SchemaValidationError(f"Anamnesis missing fields: {missing}")
        return result.payload

    def _generate_summary(
        self,
        transcript: str,
        anamnesis_json: str,
        patient_name: str,
        patient_dob: str,
        consultation_date: str,
        specialty: str,
    ) -> dict:
        user_msg = render_prompt(
            SUMMARY_USER_TEMPLATE,
            {
                "transcript": transcript,
                "anamnesis_json": anamnesis_json,
                "patient_name": patient_name,
                "patient_dob": patient_dob,
                "consultation_date": consultation_date,
                "specialty": specialty,
            },
        )
        system_prompt, user_content = enforce_role_separation(SUMMARY_SYSTEM_PROMPT, user_msg)
        result = self.llm_provider.generate_structured_output(
            "summary",
            {
                "system_prompt": system_prompt,
                "user_message": user_content,
            },
        )
        missing = ArtifactValidator.validate_summary(result.payload)
        if missing:
            raise SchemaValidationError(f"Summary missing fields: {missing}")
        return result.payload

    def _generate_insights(
        self,
        transcript: str,
        anamnesis_json: str,
        summary_json: str,
        patient_name: str,
        patient_dob: str,
        consultation_date: str,
    ) -> dict:
        user_msg = render_prompt(
            INSIGHTS_USER_TEMPLATE,
            {
                "transcript": transcript,
                "anamnesis_json": anamnesis_json,
                "summary_json": summary_json,
                "patient_name": patient_name,
                "patient_dob": patient_dob,
                "consultation_date": consultation_date,
            },
        )
        system_prompt, user_content = enforce_role_separation(INSIGHTS_SYSTEM_PROMPT, user_msg)
        result = self.llm_provider.generate_structured_output(
            "insights",
            {
                "system_prompt": system_prompt,
                "user_message": user_content,
            },
        )
        missing = ArtifactValidator.validate_insights(result.payload)
        if missing:
            raise SchemaValidationError(f"Insights missing fields: {missing}")
        unverified = EvidenceLinker.verify_evidence_in_transcript(transcript, result.payload)
        if unverified:
            logger.info(
                "insights_with_unverified_evidence",
                extra={"count": len(unverified)},
            )
        return result.payload

    def _mark_failed(self, consultation, error_msg: str) -> None:
        updated = replace(
            consultation,
            status=ConsultationStatus.PROCESSING_FAILED,
            error_details={"message": error_msg},
            updated_at=utc_now_iso(),
        )
        self.consultation_repo.save(updated)

    def _update_status(self, consultation, new_status: ConsultationStatus) -> None:
        updated = replace(
            consultation,
            status=new_status,
            updated_at=utc_now_iso(),
        )
        self.consultation_repo.save(updated)

    def _audit_failed(
        self,
        consultation_id: str,
        started_at: str,
        step: str,
        error: str,
    ) -> None:
        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.PROCESSING_FAILED,
                actor_id="system",
                timestamp=utc_now_iso(),
                payload={
                    "step": step,
                    "error": error,
                    "started_at": started_at,
                },
            )
        )

    def _audit_completed(
        self,
        consultation_id: str,
        started_at: str,
        *,
        partial: bool,
    ) -> None:
        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.PROCESSING_COMPLETED,
                actor_id="system",
                timestamp=utc_now_iso(),
                payload={
                    "started_at": started_at,
                    "partial": partial,
                },
            )
        )

    def _make_metadata(self, *, is_complete: bool) -> GenerationMetadata:
        return GenerationMetadata(
            model_name="claude",
            prompt_version="v1",
            generation_timestamp=utc_now_iso(),
            duration_ms=0,
            is_complete=is_complete,
        )
