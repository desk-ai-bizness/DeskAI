"""S3 adapter for generic artifact persistence."""

from deskai.adapters.storage.s3_artifact_keys import build_artifact_key
from deskai.adapters.storage.s3_client import S3Client
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.ports.artifact_repository import ArtifactRepository


class S3ArtifactRepository(ArtifactRepository):
    """Store and retrieve JSON artifacts in S3 using the standard key strategy."""

    def __init__(self, s3_client: S3Client) -> None:
        self._s3 = s3_client

    def save_artifact(
        self,
        clinic_id: str,
        consultation_id: str,
        artifact_type: ArtifactType,
        data: dict,
    ) -> None:
        key = build_artifact_key(clinic_id, consultation_id, artifact_type)
        self._s3.put_json(key, data)

    def get_artifact(
        self,
        clinic_id: str,
        consultation_id: str,
        artifact_type: ArtifactType,
    ) -> dict | None:
        key = build_artifact_key(clinic_id, consultation_id, artifact_type)
        return self._s3.get_json(key)
