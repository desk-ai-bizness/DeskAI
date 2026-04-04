"""Unit tests for AI pipeline domain entities."""

import unittest
from dataclasses import FrozenInstanceError

from deskai.domain.ai_pipeline.entities import PipelineResult, PipelineStatus
from deskai.domain.ai_pipeline.value_objects import ArtifactResult, GenerationMetadata
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.shared.errors import DomainValidationError


def _make_metadata(is_complete: bool = True) -> GenerationMetadata:
    return GenerationMetadata(
        model_name="gpt-4o",
        prompt_version="v1.0",
        generation_timestamp="2026-04-03T10:00:00Z",
        duration_ms=500,
        is_complete=is_complete,
    )


def _make_artifact(artifact_type: ArtifactType, is_complete: bool = True) -> ArtifactResult:
    return ArtifactResult(
        artifact_type=artifact_type,
        payload={"key": "value"},
        metadata=_make_metadata(is_complete),
        is_complete=is_complete,
    )


class PipelineStatusTest(unittest.TestCase):
    def test_running_value(self) -> None:
        self.assertEqual(PipelineStatus.RUNNING, "running")

    def test_completed_value(self) -> None:
        self.assertEqual(PipelineStatus.COMPLETED, "completed")

    def test_partially_completed_value(self) -> None:
        self.assertEqual(PipelineStatus.PARTIALLY_COMPLETED, "partially_completed")

    def test_failed_value(self) -> None:
        self.assertEqual(PipelineStatus.FAILED, "failed")

    def test_all_members(self) -> None:
        self.assertEqual(len(PipelineStatus), 4)


class PipelineResultCreationTest(unittest.TestCase):
    def test_create_minimal(self) -> None:
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.RUNNING,
        )
        self.assertEqual(pr.consultation_id, "cons-001")
        self.assertEqual(pr.clinic_id, "clinic-abc")
        self.assertEqual(pr.status, PipelineStatus.RUNNING)
        self.assertIsNone(pr.medical_history)
        self.assertIsNone(pr.summary)
        self.assertIsNone(pr.insights)
        self.assertEqual(pr.started_at, "")
        self.assertEqual(pr.completed_at, "")
        self.assertEqual(pr.error_message, "")

    def test_create_with_all_artifacts(self) -> None:
        mh = _make_artifact(ArtifactType.MEDICAL_HISTORY)
        sm = _make_artifact(ArtifactType.SUMMARY)
        ins = _make_artifact(ArtifactType.INSIGHTS)
        pr = PipelineResult(
            consultation_id="cons-002",
            clinic_id="clinic-xyz",
            status=PipelineStatus.COMPLETED,
            medical_history=mh,
            summary=sm,
            insights=ins,
            started_at="2026-04-03T10:00:00Z",
            completed_at="2026-04-03T10:05:00Z",
        )
        self.assertEqual(pr.medical_history, mh)
        self.assertEqual(pr.summary, sm)
        self.assertEqual(pr.insights, ins)
        self.assertEqual(pr.started_at, "2026-04-03T10:00:00Z")
        self.assertEqual(pr.completed_at, "2026-04-03T10:05:00Z")

    def test_frozen(self) -> None:
        pr = PipelineResult(
            consultation_id="cons-003",
            clinic_id="clinic-f",
            status=PipelineStatus.RUNNING,
        )
        with self.assertRaises(FrozenInstanceError):
            pr.status = PipelineStatus.COMPLETED


class PipelineResultValidationTest(unittest.TestCase):
    def test_empty_consultation_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            PipelineResult(
                consultation_id="",
                clinic_id="clinic-abc",
                status=PipelineStatus.RUNNING,
            )

    def test_whitespace_consultation_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            PipelineResult(
                consultation_id="   ",
                clinic_id="clinic-abc",
                status=PipelineStatus.RUNNING,
            )

    def test_empty_clinic_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            PipelineResult(
                consultation_id="cons-001",
                clinic_id="",
                status=PipelineStatus.RUNNING,
            )

    def test_whitespace_clinic_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            PipelineResult(
                consultation_id="cons-001",
                clinic_id="   ",
                status=PipelineStatus.RUNNING,
            )


class PipelineResultAllCompleteTest(unittest.TestCase):
    def test_all_complete_true(self) -> None:
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.COMPLETED,
            medical_history=_make_artifact(ArtifactType.MEDICAL_HISTORY),
            summary=_make_artifact(ArtifactType.SUMMARY),
            insights=_make_artifact(ArtifactType.INSIGHTS),
        )
        self.assertTrue(pr.all_complete())

    def test_all_complete_false_when_missing_artifact(self) -> None:
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.PARTIALLY_COMPLETED,
            medical_history=_make_artifact(ArtifactType.MEDICAL_HISTORY),
            summary=_make_artifact(ArtifactType.SUMMARY),
            insights=None,
        )
        self.assertFalse(pr.all_complete())

    def test_all_complete_false_when_artifact_incomplete(self) -> None:
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.PARTIALLY_COMPLETED,
            medical_history=_make_artifact(ArtifactType.MEDICAL_HISTORY),
            summary=_make_artifact(ArtifactType.SUMMARY, is_complete=False),
            insights=_make_artifact(ArtifactType.INSIGHTS),
        )
        self.assertFalse(pr.all_complete())

    def test_all_complete_false_when_no_artifacts(self) -> None:
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.RUNNING,
        )
        self.assertFalse(pr.all_complete())


class PipelineResultCompletedArtifactsTest(unittest.TestCase):
    def test_returns_all_when_all_present(self) -> None:
        mh = _make_artifact(ArtifactType.MEDICAL_HISTORY)
        sm = _make_artifact(ArtifactType.SUMMARY)
        ins = _make_artifact(ArtifactType.INSIGHTS)
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.COMPLETED,
            medical_history=mh,
            summary=sm,
            insights=ins,
        )
        artifacts = pr.completed_artifacts()
        self.assertEqual(len(artifacts), 3)
        self.assertIn(mh, artifacts)
        self.assertIn(sm, artifacts)
        self.assertIn(ins, artifacts)

    def test_returns_partial_when_some_none(self) -> None:
        mh = _make_artifact(ArtifactType.MEDICAL_HISTORY)
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.PARTIALLY_COMPLETED,
            medical_history=mh,
        )
        artifacts = pr.completed_artifacts()
        self.assertEqual(len(artifacts), 1)
        self.assertIn(mh, artifacts)

    def test_returns_empty_when_none(self) -> None:
        pr = PipelineResult(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            status=PipelineStatus.FAILED,
        )
        self.assertEqual(pr.completed_artifacts(), [])


if __name__ == "__main__":
    unittest.main()
