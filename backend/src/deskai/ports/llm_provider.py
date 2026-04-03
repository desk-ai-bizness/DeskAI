"""LLM provider contract."""

from abc import ABC, abstractmethod
from typing import Any

from deskai.domain.ai_pipeline.value_objects import StructuredOutput


class LLMProvider(ABC):
    """Schema-constrained generation API."""

    @abstractmethod
    def generate_structured_output(
        self,
        task: str,
        payload: dict[str, Any],
    ) -> StructuredOutput:
        """Generate a strict JSON-compatible output payload."""
