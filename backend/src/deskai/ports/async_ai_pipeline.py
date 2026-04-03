"""Async port for AI pipeline generation."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from deskai.domain.ai_pipeline.value_objects import StructuredOutput


class AsyncAIPipelinePort(ABC):
    """Async contract for AI-driven generation tasks."""

    @abstractmethod
    async def generate_streaming(
        self, task: str, payload: dict[str, Any]
    ) -> AsyncIterator[str]:
        """Yield text chunks as they are generated."""

    @abstractmethod
    async def generate_structured(
        self, task: str, payload: dict[str, Any]
    ) -> StructuredOutput:
        """Generate a complete structured output asynchronously."""
