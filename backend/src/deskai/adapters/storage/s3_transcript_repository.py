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
    ) -> dict | None:
        key = build_artifact_key(clinic_id, consultation_id, ArtifactType.TRANSCRIPT_NORMALIZED)
        result = self._s3.get_json(key)
        logger.debug(
            "transcript_normalized_fetched",
            extra=log_context(
                consultation_id=consultation_id,
                clinic_id=clinic_id,
                found=result is not None,
            ),
        )
        return result
