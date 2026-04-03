"""Unit tests for the exporter Lambda handler."""

import unittest
from types import SimpleNamespace


class ExporterHandlerTest(unittest.TestCase):
    """Tests for infra/lambda_handlers/exporter.handler."""

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

        from infra.lambda_handlers.exporter import handler

        return handler

    def test_returns_consultation_id_from_event(self) -> None:
        handler = self._import_handler()
        ctx = SimpleNamespace(aws_request_id="req-001")
        result = handler({"consultation_id": "cons-77"}, ctx)

        self.assertEqual(result["consultation_id"], "cons-77")
        self.assertEqual(result["status"], "export-placeholder-ready")

    def test_defaults_consultation_id_to_unknown(self) -> None:
        handler = self._import_handler()
        ctx = SimpleNamespace(aws_request_id="req-002")
        result = handler({}, ctx)

        self.assertEqual(result["consultation_id"], "unknown")

    def test_returns_request_id_from_context(self) -> None:
        handler = self._import_handler()
        ctx = SimpleNamespace(aws_request_id="req-abc")
        result = handler({"consultation_id": "c1"}, ctx)

        self.assertEqual(result["request_id"], "req-abc")

    def test_request_id_defaults_when_context_missing_attr(self) -> None:
        handler = self._import_handler()
        ctx = object()
        result = handler({}, ctx)

        self.assertEqual(result["request_id"], "unknown")


if __name__ == "__main__":
    unittest.main()
