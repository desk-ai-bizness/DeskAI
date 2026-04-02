"""Unit tests for the S3 artifact key strategy."""

import unittest

from deskai.adapters.storage.s3_artifact_keys import build_artifact_key
from deskai.domain.consultation.value_objects import ArtifactType


class S3ArtifactKeysTest(unittest.TestCase):
    """Tests for the pure artifact key builder."""

    def test_build_key_transcript_raw(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.TRANSCRIPT_RAW
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/transcripts/raw.json",
        )

    def test_build_key_transcript_normalized(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.TRANSCRIPT_NORMALIZED
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/transcripts/normalized.json",
        )

    def test_build_key_medical_history(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.MEDICAL_HISTORY
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/ai/medical_history.json",
        )

    def test_build_key_summary(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.SUMMARY
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/ai/summary.json",
        )

    def test_build_key_insights(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.INSIGHTS
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/ai/insights.json",
        )

    def test_build_key_physician_edits(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.PHYSICIAN_EDITS
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/review/edits.json",
        )

    def test_build_key_final_version(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.FINAL_VERSION
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/review/final.json",
        )

    def test_build_key_export_pdf(self) -> None:
        key = build_artifact_key(
            "clinic-01", "cons-001", ArtifactType.EXPORT_PDF
        )
        self.assertEqual(
            key,
            "clinics/clinic-01/consultations/cons-001/exports/final.pdf",
        )

    def test_key_follows_expected_pattern(self) -> None:
        key = build_artifact_key(
            "my-clinic", "my-cons", ArtifactType.SUMMARY
        )
        self.assertTrue(key.startswith("clinics/my-clinic/consultations/my-cons/"))

    def test_all_artifact_types_have_mapping(self) -> None:
        for artifact_type in ArtifactType:
            key = build_artifact_key("c", "x", artifact_type)
            self.assertIsInstance(key, str)
            self.assertTrue(len(key) > 0)


if __name__ == "__main__":
    unittest.main()
