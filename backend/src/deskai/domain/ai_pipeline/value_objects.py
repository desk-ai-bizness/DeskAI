"""AI pipeline domain value objects."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from deskai.domain.consultation.value_objects import ArtifactType
from deskai.shared.errors import DomainValidationError


@dataclass(frozen=True)
class StructuredOutput:
    """Immutable result of a structured LLM generation task."""

    task: str
    payload: dict[str, Any]


class InsightCategory(StrEnum):
    """Categories for consultation review insights."""

    DOCUMENTATION_GAP = "lacuna_de_documentacao"
    CONSISTENCY_ISSUE = "inconsistencia"
    CLINICAL_ATTENTION = "atencao_clinica"


class InsightSeverity(StrEnum):
    """Severity levels for consultation review insights."""

    INFORMATIVE = "informativo"
    MODERATE = "moderado"
    IMPORTANT = "importante"


@dataclass(frozen=True)
class EvidenceExcerpt:
    """Immutable excerpt from the transcript supporting an insight."""

    trecho: str
    contexto: str

    def __post_init__(self) -> None:
        if not self.trecho or not self.trecho.strip():
            raise DomainValidationError("trecho must be a non-empty string")


@dataclass(frozen=True)
class Insight:
    """Immutable consultation review insight."""

    categoria: InsightCategory
    descricao: str
    severidade: InsightSeverity
    evidencia: EvidenceExcerpt
    sugestao_revisao: str

    def __post_init__(self) -> None:
        if not self.descricao or not self.descricao.strip():
            raise DomainValidationError("descricao must be a non-empty string")


@dataclass(frozen=True)
class GenerationMetadata:
    """Immutable metadata about an LLM generation run."""

    model_name: str
    prompt_version: str
    generation_timestamp: str
    duration_ms: int
    is_complete: bool

    def __post_init__(self) -> None:
        if not self.model_name or not self.model_name.strip():
            raise DomainValidationError("model_name must be a non-empty string")
        if self.duration_ms < 0:
            raise DomainValidationError("duration_ms must be non-negative")


@dataclass(frozen=True)
class ArtifactResult:
    """Immutable result of an artifact generation step."""

    artifact_type: ArtifactType
    payload: dict[str, Any]
    metadata: GenerationMetadata
    is_complete: bool = True
