"""Finalize transcription — fetch, normalize, persist, and audit."""

from dataclasses import asdict, dataclass

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
from deskai.shared.time import utc_now_iso


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
        consultation = self.consultation_repo.find_by_id(
            consultation_id, clinic_id
        )

        try:
            raw_response = self.transcription_provider.fetch_final_transcript(
                session_id
            )
        except TranscriptionError as exc:
            self._mark_failed(consultation, str(exc))
            self.consultation_repo.save(consultation)
            raise

        self.transcript_repo.save_raw_transcript(
            clinic_id=clinic_id,
            consultation_id=consultation_id,
            raw_response=raw_response,
        )

        try:
            normalized = TranscriptionNormalizer.normalize_elevenlabs_response(
                raw_response=raw_response,
                consultation_id=consultation_id,
                provider_session_id=session_id,
            )
        except NormalizationError as exc:
            self._mark_failed(consultation, str(exc))
            self.consultation_repo.save(consultation)
            raise

        normalized_dict = asdict(normalized)
        self.transcript_repo.save_normalized_transcript(
            clinic_id=clinic_id,
            consultation_id=consultation_id,
            normalized=normalized_dict,
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
    def _mark_failed(consultation, message: str) -> None:
        """Set consultation to PROCESSING_FAILED with error details."""
        if consultation is not None:
            consultation.status = ConsultationStatus.PROCESSING_FAILED
            consultation.error_details = {"message": message}
