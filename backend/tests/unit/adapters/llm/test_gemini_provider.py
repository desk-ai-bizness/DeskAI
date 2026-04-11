"""Tests for GeminiLLMProvider — Google Gemini adapter."""

import json
import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.llm.gemini_provider import GeminiLLMProvider
from deskai.domain.ai_pipeline.exceptions import (
    GenerationError,
    SchemaValidationError,
)
from deskai.domain.ai_pipeline.value_objects import StructuredOutput


def _make_mock_response(text: str) -> MagicMock:
    """Build a mock that looks like a Gemini GenerateContentResponse."""
    response = MagicMock()
    response.text = text
    return response


class TestGeminiProviderSuccess(unittest.TestCase):
    """Happy-path generation must return a StructuredOutput."""

    def setUp(self) -> None:
        patcher = patch("deskai.adapters.llm.gemini_provider.genai")
        self.mock_genai = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_client = MagicMock()
        self.mock_genai.Client.return_value = self.mock_client

        self.provider = GeminiLLMProvider(
            api_key="test-gemini-key",
            model="gemini-2.0-flash",
        )

    def test_successful_generation_returns_structured_output(self) -> None:
        payload_data = {"diagnosis": "healthy", "confidence": 0.95}
        self.mock_client.models.generate_content.return_value = _make_mock_response(
            json.dumps(payload_data)
        )

        result = self.provider.generate_structured_output(
            task="summarize",
            payload={
                "system_prompt": "You are a medical scribe.",
                "user_message": "Summarize this consultation.",
            },
        )

        self.assertIsInstance(result, StructuredOutput)
        self.assertEqual(result.task, "summarize")
        self.assertEqual(result.payload, payload_data)

    def test_user_message_passed_as_contents(self) -> None:
        self.mock_client.models.generate_content.return_value = _make_mock_response(
            json.dumps({"result": "ok"})
        )

        self.provider.generate_structured_output(
            task="classify",
            payload={
                "system_prompt": "Be precise.",
                "user_message": "Classify this text.",
            },
        )

        call_kwargs = self.mock_client.models.generate_content.call_args[1]
        self.assertEqual(call_kwargs["model"], "gemini-2.0-flash")
        self.assertEqual(call_kwargs["contents"], "Classify this text.")

    def test_empty_system_prompt_defaults_to_empty_string(self) -> None:
        self.mock_client.models.generate_content.return_value = _make_mock_response(
            json.dumps({"result": "ok"})
        )

        self.provider.generate_structured_output(
            task="test",
            payload={"system_prompt": "", "user_message": "hello"},
        )

        config_call = self.mock_genai.types.GenerateContentConfig.call_args[1]
        self.assertEqual(config_call["system_instruction"], "")

    def test_missing_system_prompt_key_defaults_to_empty_string(self) -> None:
        self.mock_client.models.generate_content.return_value = _make_mock_response(
            json.dumps({"result": "ok"})
        )

        self.provider.generate_structured_output(
            task="test",
            payload={"user_message": "hello"},
        )

        config_call = self.mock_genai.types.GenerateContentConfig.call_args[1]
        self.assertEqual(config_call["system_instruction"], "")

    def test_api_key_passed_to_client(self) -> None:
        self.mock_genai.Client.assert_called_once_with(api_key="test-gemini-key")


class TestGeminiProviderErrors(unittest.TestCase):
    """Error handling and wrapping must produce domain exceptions."""

    def setUp(self) -> None:
        patcher = patch("deskai.adapters.llm.gemini_provider.genai")
        self.mock_genai = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_client = MagicMock()
        self.mock_genai.Client.return_value = self.mock_client

        self.provider = GeminiLLMProvider(
            api_key="test-gemini-key",
            model="gemini-2.0-flash",
        )

    def test_invalid_json_response_raises_schema_validation_error(self) -> None:
        self.mock_client.models.generate_content.return_value = _make_mock_response(
            "this is not json at all"
        )

        with self.assertRaises(SchemaValidationError):
            self.provider.generate_structured_output(
                task="test",
                payload={"system_prompt": "sys", "user_message": "usr"},
            )

    def test_api_error_wraps_in_generation_error(self) -> None:
        self.mock_client.models.generate_content.side_effect = Exception(
            "Gemini API error: quota exceeded"
        )

        with self.assertRaises(GenerationError):
            self.provider.generate_structured_output(
                task="test",
                payload={"system_prompt": "sys", "user_message": "usr"},
            )


class TestGeminiProviderRetry(unittest.TestCase):
    """Retry decorator must be present on generate_structured_output."""

    def test_retry_decorator_is_present(self) -> None:
        self.assertTrue(hasattr(GeminiLLMProvider.generate_structured_output, "retry"))


class TestGeminiProviderIsLLMProvider(unittest.TestCase):
    """GeminiLLMProvider must implement the LLMProvider port."""

    def test_is_instance_of_llm_provider(self) -> None:
        from deskai.ports.llm_provider import LLMProvider

        with patch("deskai.adapters.llm.gemini_provider.genai"):
            provider = GeminiLLMProvider(api_key="key")
        self.assertIsInstance(provider, LLMProvider)


if __name__ == "__main__":
    unittest.main()
