"""Gemini LLM provider adapter — Google GenAI API."""

from typing import Any

from google import genai
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


class GeminiLLMProvider(LLMProvider):
    """LLMProvider backed by Google's Gemini API.

    Retries on transient connection errors.
    Non-retryable API errors are wrapped in ``GenerationError``.
    Invalid JSON responses are wrapped in ``SchemaValidationError``.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    def generate_structured_output(
        self,
        task: str,
        payload: dict[str, Any],
    ) -> StructuredOutput:
        """Call Gemini and parse a strict JSON response."""
        system_prompt = payload.get("system_prompt", "")
        user_message = payload.get("user_message", "")

        logger.info(
            "gemini_llm_generating",
            extra={"task": task, "model": self._model_name},
        )

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=user_message,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
        except (ConnectionError, TimeoutError):
            raise  # let tenacity retry
        except Exception as exc:
            raise GenerationError(f"Gemini API error for task '{task}': {exc}") from exc

        raw_text = response.text

        try:
            parsed = validate_json_output(raw_text)
        except PromptValidationError as exc:
            raise SchemaValidationError(
                f"Invalid JSON from Gemini for task '{task}': {exc}"
            ) from exc

        return StructuredOutput(task=task, payload=parsed)
