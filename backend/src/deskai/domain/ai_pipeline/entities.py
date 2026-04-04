"""AI pipeline domain entities."""

from dataclasses import dataclass
from enum import StrEnum

from deskai.domain.ai_pipeline.value_objects import ArtifactResult
from deskai.shared.errors import DomainValidationError


class PipelineStatus(StrEnum):
    """Status of a pipeline execution."""

    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


@dataclass(frozen=True)
class PipelineResult:
    """Immutable result of an AI pipeline execution for a consultation."""

    consultation_id: str
    clinic_id: str
    status: PipelineStatus
    medical_history: ArtifactResult | None = None
    summary: ArtifactResult | None = None
    insights: ArtifactResult | None = None
    started_at: str = ""
    completed_at: str = ""
    error_message: str = ""

    def __post_init__(self) -> None:
        if not self.consultation_id or not self.consultation_id.strip():
            raise DomainValidationError("consultation_id must be a non-empty string")
        if not self.clinic_id or not self.clinic_id.strip():
            raise DomainValidationError("clinic_id must be a non-empty string")

    def all_complete(self) -> bool:
        """True if all three artifacts are present and marked complete."""
        artifacts = [self.medical_history, self.summary, self.insights]
        return all(a is not None and a.is_complete for a in artifacts)

    def completed_artifacts(self) -> list[ArtifactResult]:
        """Return non-None artifacts."""
        return [a for a in [self.medical_history, self.summary, self.insights] if a is not None]
