"""Tests for stub adapters -- each must raise NotImplementedError."""

import pytest

from deskai.adapters.events.stub_publisher import StubEventPublisher
from deskai.adapters.export.stub_generator import StubExportGenerator
from deskai.adapters.llm.stub_provider import StubLLMProvider
from deskai.ports.event_publisher import EventPublisher
from deskai.ports.export_generator import ExportGenerator
from deskai.ports.llm_provider import LLMProvider


class TestStubEventPublisher:
    def test_implements_port(self):
        assert issubclass(StubEventPublisher, EventPublisher)

    def test_publish_raises_not_implemented(self):
        stub = StubEventPublisher()
        with pytest.raises(NotImplementedError, match="EventPublisher.publish"):
            stub.publish("test.event", {"key": "value"})

    def test_publish_batch_raises_not_implemented(self):
        stub = StubEventPublisher()
        with pytest.raises(NotImplementedError, match="EventPublisher.publish_batch"):
            stub.publish_batch([("test.event", {"key": "value"})])


class TestStubExportGenerator:
    def test_implements_port(self):
        assert issubclass(StubExportGenerator, ExportGenerator)

    def test_generate_raises_not_implemented(self):
        stub = StubExportGenerator()
        with pytest.raises(NotImplementedError, match="ExportGenerator.generate"):
            stub.generate(None, None)


class TestStubLLMProvider:
    def test_implements_port(self):
        assert issubclass(StubLLMProvider, LLMProvider)

    def test_generate_structured_output_raises_not_implemented(self):
        stub = StubLLMProvider()
        with pytest.raises(
            NotImplementedError,
            match="LLMProvider.generate_structured_output",
        ):
            stub.generate_structured_output("summarize", {"text": "hello"})
