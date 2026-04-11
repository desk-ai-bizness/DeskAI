"""Unit tests for the AI pipeline Lambda handler."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.ai_pipeline.entities import PipelineResult, PipelineStatus
from deskai.domain.ai_pipeline.exceptions import PipelineStepError

_HANDLER_MODULE = "deskai.handlers.step_functions.run_ai_pipeline_handler"


class TestPipelineHandler(unittest.TestCase):
    """Tests for the run_ai_pipeline_handler."""

    def _import_handler(self):
        from deskai.handlers.step_functions.run_ai_pipeline_handler import (
            handler,
        )

        return handler

    @patch(f"{_HANDLER_MODULE}.build_container")
    def test_missing_consultation_id_raises_value_error(self, mock_build) -> None:
        handler_fn = self._import_handler()
        with self.assertRaises(ValueError):
            handler_fn({"clinic_id": "clinic-001"}, None)

    @patch(f"{_HANDLER_MODULE}.build_container")
    def test_missing_clinic_id_raises_value_error(self, mock_build) -> None:
        handler_fn = self._import_handler()
        with self.assertRaises(ValueError):
            handler_fn({"consultation_id": "cons-001"}, None)

    @patch(f"{_HANDLER_MODULE}.build_container")
    def test_successful_pipeline_returns_status_and_artifact_count(self, mock_build) -> None:
        handler_fn = self._import_handler()
        mock_result = MagicMock(spec=PipelineResult)
        mock_result.consultation_id = "cons-001"
        mock_result.status = PipelineStatus.COMPLETED
        mock_result.completed_artifacts.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_result.error_message = None

        container = MagicMock()
        container.run_pipeline.execute.return_value = mock_result
        mock_build.return_value = container

        result = handler_fn(
            {"consultation_id": "cons-001", "clinic_id": "clinic-001"},
            None,
        )

        self.assertEqual(result["consultation_id"], "cons-001")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["artifacts_generated"], 3)

    @patch(f"{_HANDLER_MODULE}.build_container")
    def test_eventbridge_shaped_event_is_supported(self, mock_build) -> None:
        handler_fn = self._import_handler()
        mock_result = MagicMock(spec=PipelineResult)
        mock_result.consultation_id = "cons-001"
        mock_result.status = PipelineStatus.COMPLETED
        mock_result.completed_artifacts.return_value = [MagicMock()]
        mock_result.error_message = None

        container = MagicMock()
        container.run_pipeline.execute.return_value = mock_result
        mock_build.return_value = container

        event = {
            "detail-type": "consultation.session.ended",
            "detail": {"consultation_id": "cons-001", "clinic_id": "clinic-001"},
        }

        result = handler_fn(event, None)

        self.assertEqual(result["consultation_id"], "cons-001")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["artifacts_generated"], 1)
        container.run_pipeline.execute.assert_called_once_with(
            consultation_id="cons-001", clinic_id="clinic-001"
        )

    @patch(f"{_HANDLER_MODULE}.build_container")
    def test_pipeline_error_is_raised(self, mock_build) -> None:
        handler_fn = self._import_handler()
        container = MagicMock()
        container.run_pipeline.execute.side_effect = PipelineStepError(
            "Consultation not found", "prerequisites", "not_found"
        )
        mock_build.return_value = container

        with self.assertRaises(PipelineStepError):
            handler_fn(
                {"consultation_id": "cons-001", "clinic_id": "clinic-001"},
                None,
            )

    @patch(f"{_HANDLER_MODULE}.build_container")
    def test_unexpected_exception_is_raised(self, mock_build) -> None:
        handler_fn = self._import_handler()
        container = MagicMock()
        container.run_pipeline.execute.side_effect = RuntimeError("something broke")
        mock_build.return_value = container

        with self.assertRaises(RuntimeError):
            handler_fn(
                {"consultation_id": "cons-001", "clinic_id": "clinic-001"},
                None,
            )


if __name__ == "__main__":
    unittest.main()
