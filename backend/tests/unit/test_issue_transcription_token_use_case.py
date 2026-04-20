"""Unit tests for IssueTranscriptionTokenUseCase."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.session.exceptions import InvalidSessionStateError
from tests.conftest import make_sample_consultation

_MOD = "deskai.application.transcription.issue_transcription_token"


class IssueTranscriptionTokenUseCaseTest(unittest.TestCase):
    def setUp(self):
        self.consultation_repo = MagicMock()
        self.token_provider = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.transcription.issue_transcription_token import (
            IssueTranscriptionTokenUseCase,
        )

        self.use_case = IssueTranscriptionTokenUseCase(
            consultation_repo=self.consultation_repo,
            transcription_token_provider=self.token_provider,
            audit_repo=self.audit_repo,
        )

    @patch(f"{_MOD}.new_uuid", return_value="evt-001")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T10:00:00+00:00")
    def test_success(self, _mock_time, _mock_uuid):
        consultation = make_sample_consultation(status=ConsultationStatus.RECORDING)
        self.consultation_repo.find_by_id.return_value = consultation
        self.token_provider.create_single_use_token.return_value = {
            "token": "el-token-123",
            "websocket_url": "wss://api.elevenlabs.io/v1/speech-to-text/realtime",
            "model_id": "scribe_v2_realtime",
            "language_code": "pt",
            "expires_at": "2026-04-02T10:15:00+00:00",
            "expires_in_seconds": 900,
        }

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result["token"], "el-token-123")
        self.assertEqual(result["expires_in_seconds"], 900)
        self.token_provider.create_single_use_token.assert_called_once()
        self.audit_repo.append.assert_called_once()

    def test_consultation_not_found(self):
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute(
                consultation_id="cons-missing",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    def test_wrong_doctor(self):
        consultation = make_sample_consultation(
            doctor_id="doc-other",
            status=ConsultationStatus.RECORDING,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    def test_not_recording_state(self):
        consultation = make_sample_consultation(status=ConsultationStatus.STARTED)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(InvalidSessionStateError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )


if __name__ == "__main__":
    unittest.main()
