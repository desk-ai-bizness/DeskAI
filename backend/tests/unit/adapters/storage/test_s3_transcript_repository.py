"""Unit tests for the S3TranscriptRepository adapter."""

import unittest
from unittest.mock import MagicMock

from deskai.adapters.storage.s3_transcript_repository import (
    S3TranscriptRepository,
)


class S3TranscriptRepositoryTest(unittest.TestCase):
    """Tests for S3TranscriptRepository with a mocked S3Client."""

    def setUp(self) -> None:
        self.mock_s3_client = MagicMock(name="s3-client")
        self.repo = S3TranscriptRepository(s3_client=self.mock_s3_client)

    # ---- save_raw_transcript ----

    def test_save_raw_transcript_stores_with_raw_key(self) -> None:
        raw = {"provider": "elevenlabs", "utterances": [{"text": "hello"}]}

        self.repo.save_raw_transcript(
            clinic_id="clinic-01",
            consultation_id="cons-001",
            raw_response=raw,
        )

        expected_key = (
            "clinics/clinic-01/consultations/cons-001/transcripts/raw.json"
        )
        self.mock_s3_client.put_json.assert_called_once_with(
            expected_key, raw
        )

    def test_save_raw_transcript_different_ids(self) -> None:
        raw = {"data": "test"}

        self.repo.save_raw_transcript(
            clinic_id="clinic-99",
            consultation_id="cons-xyz",
            raw_response=raw,
        )

        expected_key = (
            "clinics/clinic-99/consultations/cons-xyz/transcripts/raw.json"
        )
        self.mock_s3_client.put_json.assert_called_once_with(
            expected_key, raw
        )

    # ---- save_normalized_transcript ----

    def test_save_normalized_transcript_stores_with_normalized_key(
        self,
    ) -> None:
        normalized = {
            "segments": [
                {"speaker": "doctor", "text": "Como voce esta?"}
            ]
        }

        self.repo.save_normalized_transcript(
            clinic_id="clinic-01",
            consultation_id="cons-001",
            normalized=normalized,
        )

        expected_key = (
            "clinics/clinic-01/consultations/cons-001/"
            "transcripts/normalized.json"
        )
        self.mock_s3_client.put_json.assert_called_once_with(
            expected_key, normalized
        )

    def test_save_normalized_transcript_different_ids(self) -> None:
        normalized = {"segments": []}

        self.repo.save_normalized_transcript(
            clinic_id="clinic-42",
            consultation_id="cons-abc",
            normalized=normalized,
        )

        expected_key = (
            "clinics/clinic-42/consultations/cons-abc/"
            "transcripts/normalized.json"
        )
        self.mock_s3_client.put_json.assert_called_once_with(
            expected_key, normalized
        )

    # ---- get_normalized_transcript ----

    def test_get_normalized_transcript_returns_data(self) -> None:
        expected = {"segments": [{"speaker": "patient", "text": "bem"}]}
        self.mock_s3_client.get_json.return_value = expected

        result = self.repo.get_normalized_transcript(
            clinic_id="clinic-01",
            consultation_id="cons-001",
        )

        expected_key = (
            "clinics/clinic-01/consultations/cons-001/"
            "transcripts/normalized.json"
        )
        self.mock_s3_client.get_json.assert_called_once_with(expected_key)
        self.assertEqual(result, expected)

    def test_get_normalized_transcript_returns_none_when_missing(
        self,
    ) -> None:
        self.mock_s3_client.get_json.return_value = None

        result = self.repo.get_normalized_transcript(
            clinic_id="clinic-01",
            consultation_id="cons-missing",
        )

        self.assertIsNone(result)

    def test_get_normalized_transcript_uses_correct_key(self) -> None:
        self.mock_s3_client.get_json.return_value = {}

        self.repo.get_normalized_transcript(
            clinic_id="clinic-77",
            consultation_id="cons-999",
        )

        expected_key = (
            "clinics/clinic-77/consultations/cons-999/"
            "transcripts/normalized.json"
        )
        self.mock_s3_client.get_json.assert_called_once_with(expected_key)


if __name__ == "__main__":
    unittest.main()
