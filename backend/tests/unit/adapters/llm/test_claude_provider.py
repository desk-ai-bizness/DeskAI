"""Tests for ClaudeLLMProvider — Anthropic Claude adapter."""

import json
import unittest
from unittest.mock import MagicMock, patch

import anthropic

from deskai.adapters.llm.claude_provider import ClaudeLLMProvider
from deskai.domain.ai_pipeline.exceptions import (
    GenerationError,
    SchemaValidationError,
)
from deskai.domain.ai_pipeline.value_objects import StructuredOutput


def _make_mock_response(text: str) -> MagicMock:
    """Build a mock that looks like anthropic.types.Message."""
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


class TestClaudeProviderSuccess(unittest.TestCase):
    """Happy-path generation must return a StructuredOutput."""

    def setUp(self) -> None:
        patcher = patch("deskai.adapters.llm.claude_provider.anthropic")
        self.mock_anthropic = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_client = MagicMock()
        self.mock_anthropic.Anthropic.return_value = self.mock_client
        self.mock_anthropic.APIError = anthropic.APIError
        self.mock_anthropic.APIConnectionError = anthropic.APIConnectionError
        self.mock_anthropic.RateLimitError = anthropic.RateLimitError

        self.provider = ClaudeLLMProvider(
            api_key="sk-test-key",
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
        )

    def test_successful_generation_returns_structured_output(self) -> None:
        payload_data = {"diagnosis": "healthy", "confidence": 0.95}
        self.mock_client.messages.create.return_value = _make_mock_response(
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

    def test_correct_model_and_max_tokens_passed(self) -> None:
        self.mock_client.messages.create.return_value = _make_mock_response(
            json.dumps({"ok": True})
        )

        self.provider.generate_structured_output(
            task="extract",
            payload={
                "system_prompt": "sys",
                "user_message": "usr",
            },
        )

        call_kwargs = self.mock_client.messages.create.call_args[1]
        self.assertEqual(call_kwargs["model"], "claude-sonnet-4-20250514")
        self.assertEqual(call_kwargs["max_tokens"], 2048)

    def test_system_and_user_messages_extracted_from_payload(self) -> None:
        self.mock_client.messages.create.return_value = _make_mock_response(
            json.dumps({"result": "ok"})
        )

        self.provider.generate_structured_output(
            task="classify",
            payload={
                "system_prompt": "Be precise.",
                "user_message": "Classify this text.",
            },
        )

        call_kwargs = self.mock_client.messages.create.call_args[1]
        self.assertEqual(call_kwargs["system"], "Be precise.")
        self.assertEqual(
            call_kwargs["messages"],
            [{"role": "user", "content": "Classify this text."}],
        )

    def test_empty_system_prompt_defaults_to_empty_string(self) -> None:
        self.mock_client.messages.create.return_value = _make_mock_response(
            json.dumps({"result": "ok"})
        )

        self.provider.generate_structured_output(
            task="test",
            payload={
                "system_prompt": "",
                "user_message": "hello",
            },
        )

        call_kwargs = self.mock_client.messages.create.call_args[1]
        self.assertEqual(call_kwargs["system"], "")

    def test_missing_system_prompt_key_defaults_to_empty_string(self) -> None:
        self.mock_client.messages.create.return_value = _make_mock_response(
            json.dumps({"result": "ok"})
        )

        self.provider.generate_structured_output(
            task="test",
            payload={"user_message": "hello"},
        )

        call_kwargs = self.mock_client.messages.create.call_args[1]
        self.assertEqual(call_kwargs["system"], "")


class TestClaudeProviderErrors(unittest.TestCase):
    """Error handling and wrapping must produce domain exceptions."""

    def setUp(self) -> None:
        patcher = patch("deskai.adapters.llm.claude_provider.anthropic")
        self.mock_anthropic = patcher.start()
        self.addCleanup(patcher.stop)

        self.mock_client = MagicMock()
        self.mock_anthropic.Anthropic.return_value = self.mock_client
        self.mock_anthropic.APIError = anthropic.APIError
        self.mock_anthropic.APIConnectionError = anthropic.APIConnectionError
        self.mock_anthropic.RateLimitError = anthropic.RateLimitError

        self.provider = ClaudeLLMProvider(
            api_key="sk-test-key",
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
        )

    def test_invalid_json_response_raises_schema_validation_error(self) -> None:
        self.mock_client.messages.create.return_value = _make_mock_response(
            "this is not json at all"
        )

        with self.assertRaises(SchemaValidationError):
            self.provider.generate_structured_output(
                task="test",
                payload={"system_prompt": "sys", "user_message": "usr"},
            )

    def test_api_error_wraps_in_generation_error(self) -> None:
        self.mock_client.messages.create.side_effect = anthropic.APIStatusError(
            message="Bad request",
            response=MagicMock(status_code=400, headers={}),
            body=None,
        )

        with self.assertRaises(GenerationError):
            self.provider.generate_structured_output(
                task="test",
                payload={"system_prompt": "sys", "user_message": "usr"},
            )


class TestClaudeProviderRetry(unittest.TestCase):
    """Retry decorator must be present on generate_structured_output."""

    def test_retry_decorator_is_present(self) -> None:
        self.assertTrue(hasattr(ClaudeLLMProvider.generate_structured_output, "retry"))


if __name__ == "__main__":
    unittest.main()
