"""Unit tests for the pipeline Lambda handler."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch


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

    @patch("deskai.handlers.step_functions.run_ai_pipeline_handler.handler")
    def test_delegates_to_backend_pipeline_handler(self, mock_handler) -> None:
        handler = self._import_handler()
        ctx = SimpleNamespace(aws_request_id="req-001")
        event = {"consultation_id": "cons-42", "clinic_id": "clinic-1"}
        mock_handler.return_value = {"consultation_id": "cons-42", "status": "completed"}

        result = handler(event, ctx)

        self.assertEqual(result["consultation_id"], "cons-42")
        self.assertEqual(result["status"], "completed")
        mock_handler.assert_called_once_with(event, ctx)

    @patch("deskai.handlers.step_functions.run_ai_pipeline_handler.handler")
    def test_propagates_exceptions_from_backend_handler(self, mock_handler) -> None:
        handler = self._import_handler()
        ctx = object()
        event = {"consultation_id": "cons-42", "clinic_id": "clinic-1"}
        mock_handler.side_effect = RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            handler(event, ctx)


if __name__ == "__main__":
    unittest.main()
