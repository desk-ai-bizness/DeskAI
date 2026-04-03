"""Stub adapter for LLMProvider."""

from deskai.ports.llm_provider import LLMProvider


class StubLLMProvider(LLMProvider):
    def generate_structured_output(self, task: str, payload: dict[str, object]) -> dict[str, object]:
        raise NotImplementedError("Not yet implemented: LLMProvider.generate_structured_output")
