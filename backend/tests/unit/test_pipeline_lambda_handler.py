"""Unit tests for the pipeline Lambda handler."""

import unittest
from types import SimpleNamespace


class PipelineHandlerTest(unittest.TestCase):
    """Tests for infra/lambda_handlers/pipeline.handler."""

    def _import_handler(self):
        import sys
        import types
        from pathlib import Path

        repo_root = str(Path(__file__).resolve().parents[3])
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        if "infra" not in sys.modules:
            pkg = types.ModuleType("infra")
            pkg.__path__ = [str(Path(repo_root) / "infra")]
            sys.modules["infra"] = pkg

        from infra.lambda_handlers.pipeline import handler

        return handler

    def test_returns_consultation_id_from_event(self) -> None:
        handler = self._import_handler()
        ctx = SimpleNamespace(aws_request_id="req-001")
        result = handler({"consultation_id": "cons-42"}, ctx)

        self.assertEqual(result["consultation_id"], "cons-42")
        self.assertEqual(result["status"], "processing-placeholder-complete")

    def test_defaults_consultation_id_to_unknown(self) -> None:
        handler = self._import_handler()
        ctx = SimpleNamespace(aws_request_id="req-002")
        result = handler({}, ctx)

        self.assertEqual(result["consultation_id"], "unknown")

    def test_returns_request_id_from_context(self) -> None:
        handler = self._import_handler()
        ctx = SimpleNamespace(aws_request_id="req-xyz")
        result = handler({"consultation_id": "c1"}, ctx)

        self.assertEqual(result["request_id"], "req-xyz")

    def test_request_id_defaults_when_context_missing_attr(self) -> None:
        handler = self._import_handler()
        ctx = object()  # no aws_request_id attribute
        result = handler({}, ctx)

        self.assertEqual(result["request_id"], "unknown")


if __name__ == "__main__":
    unittest.main()
