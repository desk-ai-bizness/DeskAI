"""Unit tests for the S3TranscriptRepository adapter."""

import unittest
from unittest.mock import MagicMock

from deskai.adapters.storage.s3_transcript_repository import (
    S3TranscriptRepository,
)
from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.value_objects import SpeakerSegment


def _make_normalized(
    consultation_id: str = "cons-001",
    segments: list[SpeakerSegment] | None = None,
) -> NormalizedTranscript:
    """Build a NormalizedTranscript with sensible defaults."""
    if segments is None:
        segments = [
            SpeakerSegment(
                speaker="speaker_0",
                text="Paciente relata dor.",
                start_time=0.0,
                end_time=2.0,
                confidence=0.9,
            )
        ]
    return NormalizedTranscript(
        consultation_id=consultation_id,
        provider_name="elevenlabs",
        provider_session_id="sess-001",
        language="pt-BR",
        transcript_text="Paciente relata dor.",
        speaker_segments=segments,
        created_at="2026-04-02T12:00:00+00:00",
        updated_at="2026-04-02T12:00:00+00:00",
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

        expected_key = "clinics/clinic-01/consultations/cons-001/transcripts/raw.json"
        self.mock_s3_client.put_json.assert_called_once_with(expected_key, raw)

    def test_save_raw_transcript_different_ids(self) -> None:
        raw = {"data": "test"}

        self.repo.save_raw_transcript(
            clinic_id="clinic-99",
            consultation_id="cons-xyz",
            raw_response=raw,
        )

        expected_key = "clinics/clinic-99/consultations/cons-xyz/transcripts/raw.json"
        self.mock_s3_client.put_json.assert_called_once_with(expected_key, raw)

    # ---- save_normalized_transcript ----

    def test_save_normalized_transcript_stores_with_normalized_key(
        self,
    ) -> None:
        normalized = _make_normalized(consultation_id="cons-001")

        self.repo.save_normalized_transcript(
            clinic_id="clinic-01",
            consultation_id="cons-001",
            normalized=normalized,
        )

        expected_key = "clinics/clinic-01/consultations/cons-001/transcripts/normalized.json"
        self.mock_s3_client.put_json.assert_called_once()
        call_args = self.mock_s3_client.put_json.call_args
        self.assertEqual(call_args[0][0], expected_key)

    def test_save_normalized_transcript_different_ids(self) -> None:
        normalized = _make_normalized(
            consultation_id="cons-abc",
            segments=[],
        )

        self.repo.save_normalized_transcript(
            clinic_id="clinic-42",
            consultation_id="cons-abc",
            normalized=normalized,
        )

        expected_key = "clinics/clinic-42/consultations/cons-abc/transcripts/normalized.json"
        self.mock_s3_client.put_json.assert_called_once()
        call_args = self.mock_s3_client.put_json.call_args
        self.assertEqual(call_args[0][0], expected_key)

    def test_save_normalized_transcript_converts_dataclass_to_dict(
        self,
    ) -> None:
        normalized = _make_normalized(consultation_id="cons-001")

        self.repo.save_normalized_transcript(
            clinic_id="clinic-01",
            consultation_id="cons-001",
            normalized=normalized,
        )

        call_args = self.mock_s3_client.put_json.call_args
        stored_data = call_args[0][1]
        self.assertIsInstance(stored_data, dict)
        self.assertEqual(stored_data["consultation_id"], "cons-001")
        self.assertIsInstance(stored_data["speaker_segments"][0], dict)
        self.assertEqual(stored_data["speaker_segments"][0]["speaker"], "speaker_0")

    # ---- get_normalized_transcript ----

    def test_get_normalized_transcript_returns_data(self) -> None:
        expected = {"segments": [{"speaker": "patient", "text": "bem"}]}
        self.mock_s3_client.get_json.return_value = expected

        result = self.repo.get_normalized_transcript(
            clinic_id="clinic-01",
            consultation_id="cons-001",
        )

        expected_key = "clinics/clinic-01/consultations/cons-001/transcripts/normalized.json"
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

        expected_key = "clinics/clinic-77/consultations/cons-999/transcripts/normalized.json"
        self.mock_s3_client.get_json.assert_called_once_with(expected_key)


if __name__ == "__main__":
    unittest.main()
