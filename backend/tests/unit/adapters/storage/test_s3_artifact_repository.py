"""Unit tests for the S3ArtifactRepository adapter."""

import unittest
from unittest.mock import MagicMock

from deskai.adapters.storage.s3_artifact_repository import S3ArtifactRepository
from deskai.domain.consultation.value_objects import ArtifactType


class S3ArtifactRepositoryTest(unittest.TestCase):
    """Tests for S3ArtifactRepository with a mocked S3Client."""

    def setUp(self) -> None:
        self.mock_s3_client = MagicMock(name="s3-client")
        self.repo = S3ArtifactRepository(s3_client=self.mock_s3_client)

    # ---- save_artifact ----

    def test_save_artifact_calls_put_json_with_correct_key(self) -> None:
        data = {"provider": "elevenlabs", "segments": []}

        self.repo.save_artifact(
            clinic_id="clinic-01",
            consultation_id="cons-001",
            artifact_type=ArtifactType.TRANSCRIPT_RAW,
            data=data,
        )

        expected_key = (
            "clinics/clinic-01/consultations/cons-001/transcripts/raw.json"
        )
        self.mock_s3_client.put_json.assert_called_once_with(
            expected_key, data
        )

    def test_save_artifact_uses_normalized_key(self) -> None:
        data = {"text": "normalized content"}

        self.repo.save_artifact(
            clinic_id="clinic-02",
            consultation_id="cons-002",
            artifact_type=ArtifactType.TRANSCRIPT_NORMALIZED,
            data=data,
        )

        expected_key = (
            "clinics/clinic-02/consultations/cons-002/"
            "transcripts/normalized.json"
        )
        self.mock_s3_client.put_json.assert_called_once_with(
            expected_key, data
        )

    def test_save_artifact_works_for_summary_type(self) -> None:
        data = {"summary": "patient presented with..."}

        self.repo.save_artifact(
            clinic_id="clinic-01",
            consultation_id="cons-003",
            artifact_type=ArtifactType.SUMMARY,
            data=data,
        )

        expected_key = (
            "clinics/clinic-01/consultations/cons-003/ai/summary.json"
        )
        self.mock_s3_client.put_json.assert_called_once_with(
            expected_key, data
        )

    # ---- get_artifact ----

    def test_get_artifact_returns_data_when_found(self) -> None:
        expected = {"key": "value"}
        self.mock_s3_client.get_json.return_value = expected

        result = self.repo.get_artifact(
            clinic_id="clinic-01",
            consultation_id="cons-001",
            artifact_type=ArtifactType.TRANSCRIPT_RAW,
        )

        expected_key = (
            "clinics/clinic-01/consultations/cons-001/transcripts/raw.json"
        )
        self.mock_s3_client.get_json.assert_called_once_with(expected_key)
        self.assertEqual(result, expected)

    def test_get_artifact_returns_none_when_not_found(self) -> None:
        self.mock_s3_client.get_json.return_value = None

        result = self.repo.get_artifact(
            clinic_id="clinic-01",
            consultation_id="cons-missing",
            artifact_type=ArtifactType.SUMMARY,
        )

        self.assertIsNone(result)

    def test_get_artifact_uses_correct_key_for_insights(self) -> None:
        self.mock_s3_client.get_json.return_value = {"insights": []}

        self.repo.get_artifact(
            clinic_id="clinic-05",
            consultation_id="cons-010",
            artifact_type=ArtifactType.INSIGHTS,
        )

        expected_key = (
            "clinics/clinic-05/consultations/cons-010/ai/insights.json"
        )
        self.mock_s3_client.get_json.assert_called_once_with(expected_key)


if __name__ == "__main__":
    unittest.main()
