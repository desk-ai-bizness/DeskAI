"""AI pipeline domain exceptions."""

from deskai.shared.errors import DeskAIError


class PipelineError(DeskAIError):
    """Base exception for all pipeline errors."""


class SchemaValidationError(PipelineError):
    """Raised when LLM output fails schema validation."""


class GenerationError(PipelineError):
    """Raised when an LLM generation call fails."""


class ArtifactPersistenceError(PipelineError):
    """Raised when storing an artifact fails."""


class PipelineStepError(PipelineError):
    """Raised when a specific pipeline step fails."""

    def __init__(self, message: str, step_name: str, cause: str) -> None:
        super().__init__(message)
        self.step_name = step_name
        self.cause = cause


class IncompleteOutputError(PipelineError):
    """Raised when pipeline output is missing required fields."""
