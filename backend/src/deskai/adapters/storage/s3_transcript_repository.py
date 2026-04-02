"""S3 adapter for transcript persistence."""

from deskai.adapters.storage.s3_artifact_keys import build_artifact_key
from deskai.adapters.storage.s3_client import S3Client
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.ports.transcript_repository import TranscriptRepository


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
        key = build_artifact_key(
            clinic_id, consultation_id, ArtifactType.TRANSCRIPT_RAW
        )
        self._s3.put_json(key, raw_response)

    def save_normalized_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
        normalized: dict,
    ) -> None:
        key = build_artifact_key(
            clinic_id, consultation_id, ArtifactType.TRANSCRIPT_NORMALIZED
        )
        self._s3.put_json(key, normalized)

    def get_normalized_transcript(
        self,
        clinic_id: str,
        consultation_id: str,
    ) -> dict | None:
        key = build_artifact_key(
            clinic_id, consultation_id, ArtifactType.TRANSCRIPT_NORMALIZED
        )
        return self._s3.get_json(key)
