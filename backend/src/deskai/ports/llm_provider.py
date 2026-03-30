"""LLM provider contract."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Schema-constrained generation API."""

    @abstractmethod
    def generate_structured_output(
        self,
        task: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        """Generate a strict JSON-compatible output payload."""
