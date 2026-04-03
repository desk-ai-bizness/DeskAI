"""Unit tests for stub adapters."""

import unittest

from deskai.adapters.events.stub_publisher import StubEventPublisher
from deskai.adapters.export.stub_generator import StubExportGenerator
from deskai.adapters.llm.stub_provider import StubLLMProvider


class StubAdaptersTest(unittest.TestCase):
    def test_event_publisher_raises(self):
        with self.assertRaises(NotImplementedError):
            StubEventPublisher().publish("t", {})

    def test_export_generator_raises(self):
        with self.assertRaises(NotImplementedError):
            StubExportGenerator().generate_pdf({})

    def test_llm_provider_raises(self):
        with self.assertRaises(NotImplementedError):
            StubLLMProvider().generate_structured_output("t", {})

if __name__ == "__main__":
    unittest.main()
