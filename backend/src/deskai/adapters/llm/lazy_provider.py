"""Lazy-initializing wrapper for LLMProvider.

Defers secret loading and provider construction until the first
generation method is actually called.  This prevents cold-start
failures from blocking unrelated endpoints when the provider
secret is temporarily inaccessible.
"""

from collections.abc import Callable
from typing import Any

from deskai.domain.ai_pipeline.value_objects import StructuredOutput
from deskai.ports.llm_provider import LLMProvider
from deskai.shared.logging import get_logger

logger = get_logger()


class LazyLLMProvider(LLMProvider):
    """Wraps a factory that produces the real LLMProvider.

    The factory is invoked on the first method call, not at init time.
    If the factory raises, the error propagates to the caller and the
    next call will retry (the failed result is not cached).
    """

    def __init__(self, factory: Callable[[], LLMProvider]) -> None:
        self._factory = factory
        self._delegate: LLMProvider | None = None

    def _get_delegate(self) -> LLMProvider:
        if self._delegate is None:
            logger.info("lazy_llm_provider_initializing")
            self._delegate = self._factory()
            logger.info("lazy_llm_provider_ready")
        return self._delegate

    def generate_structured_output(
        self,
        task: str,
        payload: dict[str, Any],
    ) -> StructuredOutput:
        """Delegate to the lazily-initialized provider."""
        return self._get_delegate().generate_structured_output(task, payload)
