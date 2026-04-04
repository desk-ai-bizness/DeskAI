"""Unit tests for the UpdateReview use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.review.exceptions import ReviewNotEditableError
from deskai.domain.review.value_objects import ReviewUpdate
from tests.conftest import make_sample_auth_context, make_sample_consultation

_MOD = "deskai.application.review.update_review"


class UpdateReviewUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.artifact_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.review.update_review import UpdateReviewUseCase

        self.use_case = UpdateReviewUseCase(
            consultation_repo=self.consultation_repo,
            artifact_repo=self.artifact_repo,
            audit_repo=self.audit_repo,
        )
        self.auth = make_sample_auth_context()
        self.consultation = make_sample_consultation(
            status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW
        )
        self.consultation_repo.find_by_id.return_value = self.consultation
        self.artifact_repo.get_artifact.return_value = None

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_saves_medical_history_edit(self, _mock_time, _mock_uuid) -> None:
        update = ReviewUpdate(
            medical_history={"queixa_principal": {"descricao": "Edited"}},
        )

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
            update=update,
        )

        self.artifact_repo.save_artifact.assert_called_once()
        saved = self.artifact_repo.save_artifact.call_args
        self.assertEqual(saved[0][2], ArtifactType.PHYSICIAN_EDITS)
        self.assertIn("medical_history", saved[0][3])

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_saves_summary_edit(self, _mock_time, _mock_uuid) -> None:
        update = ReviewUpdate(
            summary={"subjetivo": {"queixa_principal": "Edited summary"}},
        )

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
            update=update,
        )

        saved_data = self.artifact_repo.save_artifact.call_args[0][3]
        self.assertIn("summary", saved_data)
        self.assertEqual(
            saved_data["summary"]["subjetivo"]["queixa_principal"],
            "Edited summary",
        )

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_saves_insight_actions(self, _mock_time, _mock_uuid) -> None:
        actions = [
            {"insight_id": "0", "action": "accepted"},
            {"insight_id": "1", "action": "dismissed"},
        ]
        update = ReviewUpdate(insight_actions=actions)

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
            update=update,
        )

        saved_data = self.artifact_repo.save_artifact.call_args[0][3]
        self.assertEqual(saved_data["insight_actions"], actions)

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_records_audit_event_per_edited_field(self, _mock_time, _mock_uuid) -> None:
        update = ReviewUpdate(
            medical_history={"edited": True},
            summary={"edited": True},
        )

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
            update=update,
        )

        # Two fields edited -> two REVIEW_EDITED audit events
        review_edit_calls = [
            c
            for c in self.audit_repo.append.call_args_list
            if c[0][0].event_type == AuditAction.REVIEW_EDITED
        ]
        self.assertEqual(len(review_edit_calls), 2)

        payloads = [c[0][0].payload for c in review_edit_calls]
        edited_fields = [p["edited_field"] for p in payloads]
        self.assertIn("medical_history", edited_fields)
        self.assertIn("summary", edited_fields)

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_records_audit_event_per_insight_action(self, _mock_time, _mock_uuid) -> None:
        actions = [
            {"insight_id": "0", "action": "accepted"},
            {"insight_id": "1", "action": "dismissed"},
        ]
        update = ReviewUpdate(insight_actions=actions)

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
            update=update,
        )

        insight_calls = [
            c
            for c in self.audit_repo.append.call_args_list
            if c[0][0].event_type == AuditAction.INSIGHT_ACTIONED
        ]
        self.assertEqual(len(insight_calls), 2)

    def test_raises_not_found_for_missing_consultation(self) -> None:
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-missing",
                clinic_id="clinic-001",
                update=ReviewUpdate(medical_history={"x": 1}),
            )

    def test_raises_ownership_error_for_wrong_doctor(self) -> None:
        consultation = make_sample_consultation(
            doctor_id="doc-other",
            status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
                update=ReviewUpdate(medical_history={"x": 1}),
            )

    def test_raises_not_editable_for_finalized_status(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.FINALIZED)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ReviewNotEditableError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
                update=ReviewUpdate(medical_history={"x": 1}),
            )

    def test_raises_not_editable_for_draft_generated_status(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.DRAFT_GENERATED)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ReviewNotEditableError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
                update=ReviewUpdate(medical_history={"x": 1}),
            )

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_merges_with_existing_edits(self, _mock_time, _mock_uuid) -> None:
        existing_edits = {
            "medical_history": {"old": "data"},
            "last_edited_at": "2026-04-01T11:00:00+00:00",
            "last_edited_by": "doc-001",
        }
        self.artifact_repo.get_artifact.return_value = existing_edits

        update = ReviewUpdate(
            summary={"subjetivo": {"queixa_principal": "New summary"}},
        )

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
            update=update,
        )

        saved_data = self.artifact_repo.save_artifact.call_args[0][3]
        # Old medical_history preserved
        self.assertEqual(saved_data["medical_history"], {"old": "data"})
        # New summary added
        self.assertIn("summary", saved_data)
        # Timestamps updated
        self.assertEqual(saved_data["last_edited_at"], "2026-04-01T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
