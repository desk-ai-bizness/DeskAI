"""Thin helper for persisting validated pipeline artifacts."""

from typing import Any

from deskai.domain.ai_pipeline.exceptions import ArtifactPersistenceError
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.ports.artifact_repository import ArtifactRepository


def store_pipeline_artifact(
    artifact_repo: ArtifactRepository,
    clinic_id: str,
    consultation_id: str,
    artifact_type: ArtifactType,
    payload: dict[str, Any],
) -> None:
    """Persist a single artifact, wrapping storage errors."""
    try:
        artifact_repo.save_artifact(clinic_id, consultation_id, artifact_type, payload)
    except Exception as exc:
        raise ArtifactPersistenceError(f"Failed to store {artifact_type.value}: {exc}") from exc
