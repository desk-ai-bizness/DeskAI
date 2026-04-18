"""S3 adapter for transcript persistence."""

from dataclasses import asdict

from deskai.adapters.storage.s3_artifact_keys import build_artifact_key
from deskai.adapters.storage.s3_client import S3Client
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.ports.transcript_repository import TranscriptRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class S3TranscriptRepository(TranscriptRepository):
    """Store and retrieve raw/normalized transcripts in S3."""

    def __init__(self, s3_client: S3Client) -> None:
        self._s3 = s3_client

    def save_raw_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
        raw_response: dict,
    ) -> None:
        key = build_artifact_key(clinic_id, consultation_id, ArtifactType.TRANSCRIPT_RAW)
        self._s3.put_json(key, raw_response)
        logger.info(
            "transcript_raw_saved",
            extra=log_context(consultation_id=consultation_id, clinic_id=clinic_id),
        )

    def save_normalized_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
        normalized: NormalizedTranscript,
    ) -> None:
        key = build_artifact_key(clinic_id, consultation_id, ArtifactType.TRANSCRIPT_NORMALIZED)
        self._s3.put_json(key, asdict(normalized))
        logger.info(
            "transcript_normalized_saved",
            extra=log_context(consultation_id=consultation_id, clinic_id=clinic_id),
        )

    def get_normalized_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
    ) -> NormalizedTranscript | None:
        key = build_artifact_key(clinic_id, consultation_id, ArtifactType.TRANSCRIPT_NORMALIZED)
        data = self._s3.get_json(key)
        logger.debug(
            "transcript_normalized_fetched",
            extra=log_context(
                consultation_id=consultation_id,
                clinic_id=clinic_id,
                found=data is not None,
            ),
        )
        if data is None:
            return None
        from deskai.domain.transcription.value_objects import (
            CompletenessStatus,
            SpeakerSegment,
        )

        return NormalizedTranscript(
            consultation_id=data["consultation_id"],
            provider_name=data["provider_name"],
            provider_session_id=data["provider_session_id"],
            language=data["language"],
            transcript_text=data["transcript_text"],
            speaker_segments=[SpeakerSegment(**seg) for seg in data.get("speaker_segments", [])],
            timestamps=data.get("timestamps"),
            confidence_metadata=data.get("confidence_metadata"),
            completeness_status=CompletenessStatus(data.get("completeness_status", "pending")),
            raw_response_key=data.get("raw_response_key"),
            normalized_artifact_key=data.get("normalized_artifact_key"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
