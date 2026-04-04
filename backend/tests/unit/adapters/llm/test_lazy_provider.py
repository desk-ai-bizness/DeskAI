"""Tests for LazyLLMProvider — deferred initialization wrapper."""

import unittest
from unittest.mock import MagicMock

from deskai.adapters.llm.lazy_provider import LazyLLMProvider
from deskai.domain.ai_pipeline.value_objects import StructuredOutput
from deskai.ports.llm_provider import LLMProvider


def _make_mock_provider() -> LLMProvider:
    """Create a mock that satisfies the LLMProvider interface."""
    mock = MagicMock(spec=LLMProvider)
    mock.generate_structured_output.return_value = StructuredOutput(
        task="test", payload={"result": "ok"}
    )
    return mock


class TestLazyLLMProviderInitialization(unittest.TestCase):
    """Factory must NOT be called until a provider method is invoked."""

    def test_factory_not_called_on_init(self) -> None:
        factory = MagicMock(return_value=_make_mock_provider())
        LazyLLMProvider(factory)
        factory.assert_not_called()

    def test_factory_called_on_first_method(self) -> None:
        factory = MagicMock(return_value=_make_mock_provider())
        lazy = LazyLLMProvider(factory)
        lazy.generate_structured_output("task", {"user_message": "hi"})
        factory.assert_called_once()

    def test_factory_called_only_once_across_multiple_calls(self) -> None:
        factory = MagicMock(return_value=_make_mock_provider())
        lazy = LazyLLMProvider(factory)
        lazy.generate_structured_output("task1", {"user_message": "a"})
        lazy.generate_structured_output("task2", {"user_message": "b"})
        lazy.generate_structured_output("task3", {"user_message": "c"})
        factory.assert_called_once()


class TestLazyLLMProviderDelegation(unittest.TestCase):
    """All LLMProvider methods must delegate to the real provider."""

    def setUp(self) -> None:
        self.delegate = _make_mock_provider()
        self.lazy = LazyLLMProvider(lambda: self.delegate)

    def test_generate_structured_output_delegates(self) -> None:
        payload = {"system_prompt": "sys", "user_message": "usr"}
        result = self.lazy.generate_structured_output("my_task", payload)

        self.delegate.generate_structured_output.assert_called_once_with("my_task", payload)
        self.assertEqual(result, self.delegate.generate_structured_output.return_value)


class TestLazyLLMProviderErrorPropagation(unittest.TestCase):
    """Factory errors must propagate at call time, not init time."""

    def test_factory_exception_propagates_on_first_call(self) -> None:
        factory = MagicMock(side_effect=RuntimeError("secret fetch failed"))
        lazy = LazyLLMProvider(factory)

        with self.assertRaises(RuntimeError, msg="secret fetch failed"):
            lazy.generate_structured_output("task", {"user_message": "hi"})


class TestLazyLLMProviderIsLLMProvider(unittest.TestCase):
    """LazyLLMProvider must satisfy the LLMProvider contract."""

    def test_is_instance_of_llm_provider(self) -> None:
        lazy = LazyLLMProvider(lambda: _make_mock_provider())
        self.assertIsInstance(lazy, LLMProvider)


if __name__ == "__main__":
    unittest.main()
