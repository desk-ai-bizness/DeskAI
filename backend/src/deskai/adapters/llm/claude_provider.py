"""Claude LLM provider adapter — Anthropic Messages API."""

from typing import Any

import anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from deskai.domain.ai_pipeline.exceptions import (
    GenerationError,
    SchemaValidationError,
)
from deskai.domain.ai_pipeline.value_objects import StructuredOutput
from deskai.ports.llm_provider import LLMProvider
from deskai.prompts.prompt_loader import PromptValidationError, validate_json_output
from deskai.shared.logging import get_logger

logger = get_logger()


class ClaudeLLMProvider(LLMProvider):
    """LLMProvider backed by Anthropic's Claude Messages API.

    Retries on transient connection and rate-limit errors.
    Non-retryable API errors are wrapped in ``GenerationError``.
    Invalid JSON responses are wrapped in ``SchemaValidationError``.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((anthropic.APIConnectionError, anthropic.RateLimitError)),
        reraise=True,
    )
    def generate_structured_output(
        self,
        task: str,
        payload: dict[str, Any],
    ) -> StructuredOutput:
        """Call Claude and parse a strict JSON response.

        Args:
            task: Identifier for the generation task (e.g. ``"summarize"``).
            payload: Must contain ``"user_message"``; may contain
                ``"system_prompt"``.

        Returns:
            A ``StructuredOutput`` with the parsed JSON payload.

        Raises:
            GenerationError: On non-retryable Anthropic API errors.
            SchemaValidationError: When the model output is not valid JSON.
        """
        system_prompt = payload.get("system_prompt", "")
        user_message = payload.get("user_message", "")

        logger.info(
            "claude_llm_generating",
            extra={"task": task, "model": self._model},
        )

        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
        except (anthropic.APIConnectionError, anthropic.RateLimitError):
            raise  # let tenacity retry
        except anthropic.APIError as exc:
            raise GenerationError(f"Claude API error for task '{task}': {exc}") from exc

        raw_text = response.content[0].text

        try:
            parsed = validate_json_output(raw_text)
        except PromptValidationError as exc:
            raise SchemaValidationError(
                f"Invalid JSON from Claude for task '{task}': {exc}"
            ) from exc

        return StructuredOutput(task=task, payload=parsed)
