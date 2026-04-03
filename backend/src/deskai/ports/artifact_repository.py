"""Port interface for artifact persistence."""

from abc import ABC, abstractmethod
from typing import Any

from deskai.domain.consultation.value_objects import ArtifactType


class ArtifactRepository(ABC):
    """Persistence contract for consultation artifacts in object storage."""

    @abstractmethod
    def save_artifact(
        self,
        clinic_id: str,
        consultation_id: str,
        artifact_type: ArtifactType,
        data: dict[str, Any],
    ) -> None:
        """Persist a JSON-serializable artifact."""

    @abstractmethod
    def get_artifact(
        self,
        clinic_id: str,
        consultation_id: str,
        artifact_type: ArtifactType,
    ) -> dict[str, Any] | None:
        """Load a previously stored artifact, or None if not found."""
