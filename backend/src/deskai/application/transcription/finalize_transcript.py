"""Finalize transcription — fetch, normalize, persist, and audit."""

from dataclasses import dataclass, replace

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.exceptions import (
    NormalizationError,
    TranscriptionError,
)
from deskai.domain.transcription.services import TranscriptionNormalizer
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.transcript_repository import TranscriptRepository
from deskai.ports.transcription_provider import TranscriptionProvider
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


@dataclass(frozen=True)
class FinalizeTranscriptUseCase:
    """Fetch final transcript from provider, normalize, persist, and audit."""

    transcription_provider: TranscriptionProvider
    transcript_repo: TranscriptRepository
    consultation_repo: ConsultationRepository
    audit_repo: AuditRepository

    def execute(
        self,
        session_id: str,
        consultation_id: str,
        clinic_id: str,
    ) -> NormalizedTranscript:
        logger.info(
            "transcript_finalization_started",
            extra=log_context(
                session_id=session_id, consultation_id=consultation_id, clinic_id=clinic_id,
            ),
        )

        consultation = self.consultation_repo.find_by_id(
            consultation_id, clinic_id
        )

        try:
            raw_response = self.transcription_provider.fetch_final_transcript(
                session_id
            )
        except TranscriptionError as exc:
            logger.error(
                "transcript_fetch_failed",
                extra=log_context(
                    session_id=session_id, consultation_id=consultation_id, error=str(exc),
                ),
            )
            consultation = self._mark_failed(consultation, str(exc))
            self.consultation_repo.save(consultation)
            raise

        self.transcript_repo.save_raw_transcript(
            clinic_id=clinic_id,
            consultation_id=consultation_id,
            raw_response=raw_response,
        )
        logger.info(
            "raw_transcript_saved",
            extra=log_context(consultation_id=consultation_id, session_id=session_id),
        )

        try:
            normalized = TranscriptionNormalizer.normalize_elevenlabs_response(
                raw_response=raw_response,
                consultation_id=consultation_id,
                provider_session_id=session_id,
            )
        except NormalizationError as exc:
            logger.error(
                "transcript_normalization_failed",
                extra=log_context(
                    session_id=session_id, consultation_id=consultation_id, error=str(exc),
                ),
            )
            consultation = self._mark_failed(consultation, str(exc))
            self.consultation_repo.save(consultation)
            raise

        self.transcript_repo.save_normalized_transcript(
            clinic_id=clinic_id,
            consultation_id=consultation_id,
            normalized=normalized,
        )
        logger.info(
            "transcript_finalized",
            extra=log_context(
                consultation_id=consultation_id,
                completeness=str(normalized.completeness_status),
            ),
        )

        now = utc_now_iso()
        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.PROCESSING_STARTED,
                actor_id="system",
                timestamp=now,
                payload={
                    "session_id": session_id,
                    "provider": "elevenlabs",
                    "completeness": str(normalized.completeness_status),
                },
            )
        )

        return normalized

    @staticmethod
    def _mark_failed(consultation, message: str):
        """Return a new consultation marked PROCESSING_FAILED."""
        if consultation is not None:
            return replace(
                consultation,
                status=ConsultationStatus.PROCESSING_FAILED,
                error_details={"message": message},
            )
        return consultation
