"""Unit tests for the OpenReview use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.review.exceptions import ReviewNotAvailableError
from tests.conftest import make_sample_auth_context, make_sample_consultation

_MOD = "deskai.application.review.open_review"


class OpenReviewUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.artifact_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.review.open_review import OpenReviewUseCase

        self.use_case = OpenReviewUseCase(
            consultation_repo=self.consultation_repo,
            artifact_repo=self.artifact_repo,
            audit_repo=self.audit_repo,
        )
        self.auth = make_sample_auth_context()

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_opens_review_for_draft_generated_transitions_to_under_review(
        self, _mock_time, _mock_uuid
    ) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.DRAFT_GENERATED)
        self.consultation_repo.find_by_id.return_value = consultation
        self.artifact_repo.get_artifact.return_value = None

        result = self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        # Verify transition was saved
        saved = self.consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.status, ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.assertEqual(saved.review_opened_at, "2026-04-01T12:00:00+00:00")

        self.assertEqual(result.consultation_id, "cons-001")

    def test_opens_review_for_already_under_review_no_transition(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation
        self.artifact_repo.get_artifact.return_value = None

        result = self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        # No save should occur (no transition needed)
        self.consultation_repo.save.assert_not_called()
        self.assertEqual(result.consultation_id, "cons-001")

    def test_raises_not_found_for_missing_consultation(self) -> None:
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-missing",
                clinic_id="clinic-001",
            )

    def test_raises_ownership_error_for_wrong_doctor(self) -> None:
        consultation = make_sample_consultation(
            doctor_id="doc-other",
            status=ConsultationStatus.DRAFT_GENERATED,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    def test_raises_review_not_available_for_started_status(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.STARTED)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ReviewNotAvailableError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    def test_raises_review_not_available_for_in_processing_status(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.IN_PROCESSING)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ReviewNotAvailableError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_loads_edited_artifacts_when_edits_exist(self, _mock_time, _mock_uuid) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation

        edited_history = {"queixa_principal": {"descricao": "Edited complaint"}}
        edited_summary = {"subjetivo": {"queixa_principal": "Edited"}}

        def get_artifact_side_effect(clinic_id, consultation_id, artifact_type):
            if artifact_type == ArtifactType.MEDICAL_HISTORY:
                return {"queixa_principal": {"descricao": "Original"}}
            if artifact_type == ArtifactType.SUMMARY:
                return {"subjetivo": {"queixa_principal": "Original"}}
            if artifact_type == ArtifactType.INSIGHTS:
                return {"observacoes": []}
            if artifact_type == ArtifactType.PHYSICIAN_EDITS:
                return {
                    "medical_history": edited_history,
                    "summary": edited_summary,
                }
            return None

        self.artifact_repo.get_artifact.side_effect = get_artifact_side_effect

        result = self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.medical_history, edited_history)
        self.assertEqual(result.summary, edited_summary)
        self.assertTrue(result.medical_history_edited)
        self.assertTrue(result.summary_edited)

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T12:00:00+00:00")
    def test_records_audit_event_on_first_open(self, _mock_time, _mock_uuid) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.DRAFT_GENERATED)
        self.consultation_repo.find_by_id.return_value = consultation
        self.artifact_repo.get_artifact.return_value = None

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.audit_repo.append.assert_called_once()
        audit_event = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit_event.event_type, AuditAction.REVIEW_OPENED)
        self.assertEqual(audit_event.actor_id, "doc-001")
        self.assertEqual(audit_event.consultation_id, "cons-001")


if __name__ == "__main__":
    unittest.main()
