"""Unit tests for review domain layer."""

import unittest
from dataclasses import FrozenInstanceError

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.review.entities import (
    FinalizedRecord,
    InsightAction,
    InsightReviewItem,
    ReviewPayload,
)
from deskai.domain.review.exceptions import (
    ArtifactsIncompleteError,
    ExportNotAllowedError,
    FinalizationNotAllowedError,
    ReviewNotAvailableError,
    ReviewNotEditableError,
)
from deskai.domain.review.services import (
    is_already_finalized,
    validate_export,
    validate_finalization,
    validate_review_access,
    validate_review_editable,
)
from deskai.domain.review.value_objects import ReviewUpdate
from deskai.shared.errors import DeskAIError, DomainValidationError


# ---------------------------------------------------------------------------
# InsightAction enum
# ---------------------------------------------------------------------------
class InsightActionTest(unittest.TestCase):
    def test_pending_value(self) -> None:
        self.assertEqual(InsightAction.PENDING, "pending")

    def test_accepted_value(self) -> None:
        self.assertEqual(InsightAction.ACCEPTED, "accepted")

    def test_dismissed_value(self) -> None:
        self.assertEqual(InsightAction.DISMISSED, "dismissed")

    def test_edited_value(self) -> None:
        self.assertEqual(InsightAction.EDITED, "edited")

    def test_all_members(self) -> None:
        self.assertEqual(len(InsightAction), 4)


# ---------------------------------------------------------------------------
# InsightReviewItem entity
# ---------------------------------------------------------------------------
class InsightReviewItemCreationTest(unittest.TestCase):
    def test_create_with_defaults(self) -> None:
        item = InsightReviewItem(insight_id="ins-001")
        self.assertEqual(item.insight_id, "ins-001")
        self.assertEqual(item.action, InsightAction.PENDING)
        self.assertEqual(item.physician_note, "")

    def test_create_with_all_fields(self) -> None:
        item = InsightReviewItem(
            insight_id="ins-002",
            action=InsightAction.ACCEPTED,
            physician_note="Looks good",
        )
        self.assertEqual(item.action, InsightAction.ACCEPTED)
        self.assertEqual(item.physician_note, "Looks good")

    def test_frozen(self) -> None:
        item = InsightReviewItem(insight_id="ins-003")
        with self.assertRaises(FrozenInstanceError):
            item.action = InsightAction.DISMISSED


class InsightReviewItemValidationTest(unittest.TestCase):
    def test_empty_insight_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            InsightReviewItem(insight_id="")

    def test_whitespace_insight_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            InsightReviewItem(insight_id="   ")


# ---------------------------------------------------------------------------
# ReviewPayload entity
# ---------------------------------------------------------------------------
class ReviewPayloadCreationTest(unittest.TestCase):
    def test_create_minimal(self) -> None:
        rp = ReviewPayload(consultation_id="cons-001")
        self.assertEqual(rp.consultation_id, "cons-001")
        self.assertIsNone(rp.medical_history)
        self.assertIsNone(rp.summary)
        self.assertIsNone(rp.insights)
        self.assertIsNone(rp.transcript_segments)
        self.assertFalse(rp.medical_history_edited)
        self.assertFalse(rp.summary_edited)
        self.assertEqual(rp.insight_actions, [])
        self.assertFalse(rp.completeness_warning)

    def test_create_with_data(self) -> None:
        rp = ReviewPayload(
            consultation_id="cons-002",
            medical_history={"queixa": "dor"},
            summary={"resumo": "consulta"},
            insights=[{"id": "i1"}],
            transcript_segments=[{"start": 0}],
            medical_history_edited=True,
            summary_edited=True,
            insight_actions=[InsightReviewItem(insight_id="i1")],
            completeness_warning=True,
        )
        self.assertEqual(rp.medical_history, {"queixa": "dor"})
        self.assertTrue(rp.medical_history_edited)
        self.assertTrue(rp.completeness_warning)
        self.assertEqual(len(rp.insight_actions), 1)

    def test_frozen(self) -> None:
        rp = ReviewPayload(consultation_id="cons-003")
        with self.assertRaises(FrozenInstanceError):
            rp.consultation_id = "other"


class ReviewPayloadValidationTest(unittest.TestCase):
    def test_empty_consultation_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            ReviewPayload(consultation_id="")

    def test_whitespace_consultation_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            ReviewPayload(consultation_id="   ")


# ---------------------------------------------------------------------------
# FinalizedRecord entity
# ---------------------------------------------------------------------------
class FinalizedRecordCreationTest(unittest.TestCase):
    def test_create_valid(self) -> None:
        fr = FinalizedRecord(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            doctor_id="doc-001",
            patient_id="pat-001",
            medical_history={"queixa": "dor"},
            summary={"resumo": "ok"},
            accepted_insights=[{"id": "i1"}],
            finalized_at="2026-04-03T12:00:00Z",
            finalized_by="doc-001",
        )
        self.assertEqual(fr.consultation_id, "cons-001")
        self.assertEqual(fr.clinic_id, "clinic-abc")
        self.assertEqual(fr.doctor_id, "doc-001")
        self.assertEqual(fr.patient_id, "pat-001")
        self.assertEqual(fr.medical_history, {"queixa": "dor"})
        self.assertEqual(fr.summary, {"resumo": "ok"})
        self.assertEqual(fr.accepted_insights, [{"id": "i1"}])
        self.assertEqual(fr.finalized_at, "2026-04-03T12:00:00Z")
        self.assertEqual(fr.finalized_by, "doc-001")

    def test_frozen(self) -> None:
        fr = FinalizedRecord(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            doctor_id="doc-001",
            patient_id="pat-001",
            medical_history={},
            summary={},
            accepted_insights=[],
            finalized_at="2026-04-03T12:00:00Z",
            finalized_by="doc-001",
        )
        with self.assertRaises(FrozenInstanceError):
            fr.consultation_id = "other"


class FinalizedRecordValidationTest(unittest.TestCase):
    def _make(self, **overrides) -> FinalizedRecord:
        defaults = dict(
            consultation_id="cons-001",
            clinic_id="clinic-abc",
            doctor_id="doc-001",
            patient_id="pat-001",
            medical_history={},
            summary={},
            accepted_insights=[],
            finalized_at="2026-04-03T12:00:00Z",
            finalized_by="doc-001",
        )
        defaults.update(overrides)
        return FinalizedRecord(**defaults)

    def test_empty_consultation_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="")

    def test_whitespace_consultation_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="   ")

    def test_empty_clinic_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="")

    def test_whitespace_clinic_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="   ")

    def test_empty_doctor_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(doctor_id="")

    def test_whitespace_doctor_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(doctor_id="   ")

    def test_empty_finalized_at_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(finalized_at="")

    def test_whitespace_finalized_at_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(finalized_at="   ")

    def test_empty_finalized_by_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(finalized_by="")

    def test_whitespace_finalized_by_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            self._make(finalized_by="   ")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class ReviewExceptionsTest(unittest.TestCase):
    def test_all_exceptions_extend_deskai_error(self) -> None:
        self.assertTrue(issubclass(ReviewNotAvailableError, DeskAIError))
        self.assertTrue(issubclass(ReviewNotEditableError, DeskAIError))
        self.assertTrue(issubclass(FinalizationNotAllowedError, DeskAIError))
        self.assertTrue(issubclass(ExportNotAllowedError, DeskAIError))
        self.assertTrue(issubclass(ArtifactsIncompleteError, DeskAIError))

    def test_review_not_available_attributes(self) -> None:
        err = ReviewNotAvailableError("cons-001", "started")
        self.assertEqual(err.consultation_id, "cons-001")
        self.assertEqual(err.current_status, "started")
        self.assertIn("cons-001", str(err))
        self.assertIn("started", str(err))

    def test_review_not_editable_attributes(self) -> None:
        err = ReviewNotEditableError("cons-002", "finalized")
        self.assertEqual(err.consultation_id, "cons-002")
        self.assertEqual(err.current_status, "finalized")
        self.assertIn("cons-002", str(err))

    def test_finalization_not_allowed_attributes(self) -> None:
        err = FinalizationNotAllowedError("cons-003", "not ready")
        self.assertEqual(err.consultation_id, "cons-003")
        self.assertEqual(err.reason, "not ready")
        self.assertIn("cons-003", str(err))

    def test_export_not_allowed_attributes(self) -> None:
        err = ExportNotAllowedError("cons-004", "started")
        self.assertEqual(err.consultation_id, "cons-004")
        self.assertEqual(err.current_status, "started")
        self.assertIn("cons-004", str(err))

    def test_artifacts_incomplete_attributes(self) -> None:
        err = ArtifactsIncompleteError("cons-005", ["summary", "insights"])
        self.assertEqual(err.consultation_id, "cons-005")
        self.assertEqual(err.missing, ["summary", "insights"])
        self.assertIn("summary", str(err))
        self.assertIn("insights", str(err))


# ---------------------------------------------------------------------------
# Domain services — validate_review_access
# ---------------------------------------------------------------------------
class ValidateReviewAccessTest(unittest.TestCase):
    def test_draft_generated_allows_access(self) -> None:
        validate_review_access("cons-001", ConsultationStatus.DRAFT_GENERATED)

    def test_under_physician_review_allows_access(self) -> None:
        validate_review_access("cons-001", ConsultationStatus.UNDER_PHYSICIAN_REVIEW)

    def test_started_raises(self) -> None:
        with self.assertRaises(ReviewNotAvailableError):
            validate_review_access("cons-001", ConsultationStatus.STARTED)

    def test_recording_raises(self) -> None:
        with self.assertRaises(ReviewNotAvailableError):
            validate_review_access("cons-001", ConsultationStatus.RECORDING)

    def test_in_processing_raises(self) -> None:
        with self.assertRaises(ReviewNotAvailableError):
            validate_review_access("cons-001", ConsultationStatus.IN_PROCESSING)

    def test_processing_failed_raises(self) -> None:
        with self.assertRaises(ReviewNotAvailableError):
            validate_review_access("cons-001", ConsultationStatus.PROCESSING_FAILED)

    def test_finalized_raises(self) -> None:
        with self.assertRaises(ReviewNotAvailableError):
            validate_review_access("cons-001", ConsultationStatus.FINALIZED)


# ---------------------------------------------------------------------------
# Domain services — validate_review_editable
# ---------------------------------------------------------------------------
class ValidateReviewEditableTest(unittest.TestCase):
    def test_under_physician_review_allows_edit(self) -> None:
        validate_review_editable("cons-001", ConsultationStatus.UNDER_PHYSICIAN_REVIEW)

    def test_draft_generated_raises(self) -> None:
        with self.assertRaises(ReviewNotEditableError):
            validate_review_editable("cons-001", ConsultationStatus.DRAFT_GENERATED)

    def test_finalized_raises(self) -> None:
        with self.assertRaises(ReviewNotEditableError):
            validate_review_editable("cons-001", ConsultationStatus.FINALIZED)

    def test_started_raises(self) -> None:
        with self.assertRaises(ReviewNotEditableError):
            validate_review_editable("cons-001", ConsultationStatus.STARTED)


# ---------------------------------------------------------------------------
# Domain services — validate_finalization
# ---------------------------------------------------------------------------
class ValidateFinalizationTest(unittest.TestCase):
    def test_under_physician_review_allows_finalization(self) -> None:
        validate_finalization("cons-001", ConsultationStatus.UNDER_PHYSICIAN_REVIEW)

    def test_already_finalized_is_idempotent(self) -> None:
        validate_finalization("cons-001", ConsultationStatus.FINALIZED)

    def test_started_raises(self) -> None:
        with self.assertRaises(FinalizationNotAllowedError):
            validate_finalization("cons-001", ConsultationStatus.STARTED)

    def test_draft_generated_raises(self) -> None:
        with self.assertRaises(FinalizationNotAllowedError):
            validate_finalization("cons-001", ConsultationStatus.DRAFT_GENERATED)

    def test_in_processing_raises(self) -> None:
        with self.assertRaises(FinalizationNotAllowedError):
            validate_finalization("cons-001", ConsultationStatus.IN_PROCESSING)


# ---------------------------------------------------------------------------
# Domain services — validate_export
# ---------------------------------------------------------------------------
class ValidateExportTest(unittest.TestCase):
    def test_finalized_allows_export(self) -> None:
        validate_export("cons-001", ConsultationStatus.FINALIZED)

    def test_under_physician_review_raises(self) -> None:
        with self.assertRaises(ExportNotAllowedError):
            validate_export("cons-001", ConsultationStatus.UNDER_PHYSICIAN_REVIEW)

    def test_started_raises(self) -> None:
        with self.assertRaises(ExportNotAllowedError):
            validate_export("cons-001", ConsultationStatus.STARTED)

    def test_draft_generated_raises(self) -> None:
        with self.assertRaises(ExportNotAllowedError):
            validate_export("cons-001", ConsultationStatus.DRAFT_GENERATED)


# ---------------------------------------------------------------------------
# Domain services — is_already_finalized
# ---------------------------------------------------------------------------
class IsAlreadyFinalizedTest(unittest.TestCase):
    def test_finalized_returns_true(self) -> None:
        self.assertTrue(is_already_finalized(ConsultationStatus.FINALIZED))

    def test_under_review_returns_false(self) -> None:
        self.assertFalse(is_already_finalized(ConsultationStatus.UNDER_PHYSICIAN_REVIEW))

    def test_started_returns_false(self) -> None:
        self.assertFalse(is_already_finalized(ConsultationStatus.STARTED))


# ---------------------------------------------------------------------------
# ReviewUpdate value object
# ---------------------------------------------------------------------------
class ReviewUpdateTest(unittest.TestCase):
    def test_create_empty(self) -> None:
        ru = ReviewUpdate()
        self.assertIsNone(ru.medical_history)
        self.assertIsNone(ru.summary)
        self.assertIsNone(ru.insight_actions)

    def test_has_changes_false_when_empty(self) -> None:
        ru = ReviewUpdate()
        self.assertFalse(ru.has_changes())

    def test_has_changes_true_with_medical_history(self) -> None:
        ru = ReviewUpdate(medical_history={"queixa": "dor"})
        self.assertTrue(ru.has_changes())

    def test_has_changes_true_with_summary(self) -> None:
        ru = ReviewUpdate(summary={"resumo": "ok"})
        self.assertTrue(ru.has_changes())

    def test_has_changes_true_with_insight_actions(self) -> None:
        ru = ReviewUpdate(insight_actions=[{"id": "i1", "action": "accepted"}])
        self.assertTrue(ru.has_changes())

    def test_edited_fields_empty(self) -> None:
        ru = ReviewUpdate()
        self.assertEqual(ru.edited_fields(), [])

    def test_edited_fields_medical_history(self) -> None:
        ru = ReviewUpdate(medical_history={"queixa": "dor"})
        self.assertEqual(ru.edited_fields(), ["medical_history"])

    def test_edited_fields_summary(self) -> None:
        ru = ReviewUpdate(summary={"resumo": "ok"})
        self.assertEqual(ru.edited_fields(), ["summary"])

    def test_edited_fields_insights(self) -> None:
        ru = ReviewUpdate(insight_actions=[{"id": "i1"}])
        self.assertEqual(ru.edited_fields(), ["insights"])

    def test_edited_fields_all(self) -> None:
        ru = ReviewUpdate(
            medical_history={"a": 1},
            summary={"b": 2},
            insight_actions=[{"c": 3}],
        )
        self.assertEqual(ru.edited_fields(), ["medical_history", "summary", "insights"])

    def test_frozen(self) -> None:
        ru = ReviewUpdate()
        with self.assertRaises(FrozenInstanceError):
            ru.medical_history = {"x": 1}


if __name__ == "__main__":
    unittest.main()
