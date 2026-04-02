"""Unit tests for the FinalizeTranscript use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.transcription.exceptions import (
    NormalizationError,
    ProviderSessionError,
)
from deskai.domain.transcription.value_objects import CompletenessStatus
from tests.conftest import make_sample_consultation

_MOD = "deskai.application.transcription.finalize_transcript"


def _make_raw_response():
    return {
        "text": "Paciente relata dor de cabeca ha dois dias.",
        "language_code": "pt",
        "words": [
            {
                "text": "Paciente",
                "speaker_id": "speaker_0",
                "start": 0.0,
                "end": 0.5,
            },
            {
                "text": "relata",
                "speaker_id": "speaker_0",
                "start": 0.5,
                "end": 1.0,
            },
        ],
    }


class FinalizeTranscriptUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.transcription_provider = MagicMock()
        self.transcript_repo = MagicMock()
        self.consultation_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.transcription.finalize_transcript import (
            FinalizeTranscriptUseCase,
        )

        self.use_case = FinalizeTranscriptUseCase(
            transcription_provider=self.transcription_provider,
            transcript_repo=self.transcript_repo,
            consultation_repo=self.consultation_repo,
            audit_repo=self.audit_repo,
        )

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_successful_finalization(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        raw = _make_raw_response()
        self.transcription_provider.fetch_final_transcript.return_value = raw

        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        result = self.use_case.execute(
            session_id="sess-001",
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.provider_name, "elevenlabs")
        self.assertEqual(result.completeness_status, CompletenessStatus.COMPLETE)

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_saves_raw_transcript(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        raw = _make_raw_response()
        self.transcription_provider.fetch_final_transcript.return_value = raw
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        self.use_case.execute(
            session_id="sess-001",
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.transcript_repo.save_raw_transcript.assert_called_once_with(
            clinic_id="clinic-001",
            consultation_id="cons-001",
            raw_response=raw,
        )

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_saves_normalized_transcript(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        raw = _make_raw_response()
        self.transcription_provider.fetch_final_transcript.return_value = raw
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        self.use_case.execute(
            session_id="sess-001",
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.transcript_repo.save_normalized_transcript.assert_called_once()
        call_kwargs = self.transcript_repo.save_normalized_transcript.call_args[1]
        self.assertEqual(call_kwargs["clinic_id"], "clinic-001")
        self.assertEqual(call_kwargs["consultation_id"], "cons-001")
        normalized = call_kwargs["normalized"]
        self.assertEqual(normalized["provider_name"], "elevenlabs")

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_creates_audit_event(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        raw = _make_raw_response()
        self.transcription_provider.fetch_final_transcript.return_value = raw
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        self.use_case.execute(
            session_id="sess-001",
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.audit_repo.append.assert_called_once()
        audit_event = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit_event.consultation_id, "cons-001")
        self.assertEqual(audit_event.event_type, AuditAction.PROCESSING_STARTED)

    def test_provider_error_marks_processing_failed(self) -> None:
        self.transcription_provider.fetch_final_transcript.side_effect = (
            ProviderSessionError("Provider down")
        )
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ProviderSessionError):
            self.use_case.execute(
                session_id="sess-001",
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

        self.consultation_repo.save.assert_called_once()
        saved = self.consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.status, ConsultationStatus.PROCESSING_FAILED)

    def test_normalization_error_marks_processing_failed(self) -> None:
        raw = {"no_text_field": True}
        self.transcription_provider.fetch_final_transcript.return_value = raw
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(NormalizationError):
            self.use_case.execute(
                session_id="sess-001",
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

        self.consultation_repo.save.assert_called_once()
        saved = self.consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.status, ConsultationStatus.PROCESSING_FAILED)

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_provider_error_records_error_details(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        self.transcription_provider.fetch_final_transcript.side_effect = (
            ProviderSessionError("Connection refused")
        )
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ProviderSessionError):
            self.use_case.execute(
                session_id="sess-001",
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

        saved = self.consultation_repo.save.call_args[0][0]
        self.assertIsNotNone(saved.error_details)
        self.assertIn("Connection refused", saved.error_details["message"])

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_no_transcript_repo_calls_on_provider_error(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        self.transcription_provider.fetch_final_transcript.side_effect = (
            ProviderSessionError("fail")
        )
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ProviderSessionError):
            self.use_case.execute(
                session_id="sess-001",
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

        self.transcript_repo.save_raw_transcript.assert_not_called()
        self.transcript_repo.save_normalized_transcript.assert_not_called()


if __name__ == "__main__":
    unittest.main()
