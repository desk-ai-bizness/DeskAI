"""Unit tests for the Step Functions finalize-transcript handler."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.transcription.exceptions import TranscriptionError


class FinalizeTranscriptHandlerTest(unittest.TestCase):
    def test_success_returns_output(self):
        from deskai.handlers.step_functions.finalize_transcript_handler import (
            handler,
        )

        mock_container = MagicMock()
        mock_result = MagicMock()
        mock_result.completeness_status = "complete"
        mock_container.finalize_transcript.execute.return_value = mock_result

        with patch(
            "deskai.container.build_container",
            return_value=mock_container,
        ):
            event = {
                "session_id": "sess-001",
                "consultation_id": "cons-001",
                "clinic_id": "clinic-001",
            }

            result = handler(event, None)

        self.assertEqual(result["consultation_id"], "cons-001")
        self.assertEqual(result["status"], "transcript_finalized")
        self.assertEqual(result["completeness"], "complete")
        mock_container.finalize_transcript.execute.assert_called_once_with(
            session_id="sess-001",
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

    def test_eventbridge_shaped_payload(self):
        from deskai.handlers.step_functions.finalize_transcript_handler import (
            handler,
        )

        mock_container = MagicMock()
        mock_result = MagicMock()
        mock_result.completeness_status = "partial"
        mock_container.finalize_transcript.execute.return_value = mock_result

        with patch(
            "deskai.container.build_container",
            return_value=mock_container,
        ):
            event = {
                "detail": {
                    "session_id": "sess-002",
                    "consultation_id": "cons-002",
                    "clinic_id": "clinic-002",
                },
            }

            result = handler(event, None)

        self.assertEqual(result["consultation_id"], "cons-002")
        mock_container.finalize_transcript.execute.assert_called_once_with(
            session_id="sess-002",
            consultation_id="cons-002",
            clinic_id="clinic-002",
        )

    def test_missing_fields_raises(self):
        from deskai.handlers.step_functions.finalize_transcript_handler import (
            handler,
        )

        with patch(
            "deskai.container.build_container",
        ):
            with self.assertRaises(ValueError):
                handler({}, None)

    def test_transcription_error_propagates(self):
        from deskai.handlers.step_functions.finalize_transcript_handler import (
            handler,
        )

        mock_container = MagicMock()
        mock_container.finalize_transcript.execute.side_effect = TranscriptionError(
            "provider failed"
        )

        with patch(
            "deskai.container.build_container",
            return_value=mock_container,
        ):
            with self.assertRaises(TranscriptionError):
                handler(
                    {
                        "session_id": "sess-001",
                        "consultation_id": "cons-001",
                        "clinic_id": "clinic-001",
                    },
                    None,
                )


if __name__ == "__main__":
    unittest.main()
