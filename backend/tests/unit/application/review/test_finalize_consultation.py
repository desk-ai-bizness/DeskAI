"""Unit tests for the FinalizeConsultation use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.review.exceptions import FinalizationNotAllowedError
from tests.conftest import make_sample_auth_context, make_sample_consultation

_MOD = "deskai.application.review.finalize_consultation"


class FinalizeConsultationUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.artifact_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.review.finalize_consultation import (
            FinalizeConsultationUseCase,
        )

        self.use_case = FinalizeConsultationUseCase(
            consultation_repo=self.consultation_repo,
            artifact_repo=self.artifact_repo,
            audit_repo=self.audit_repo,
        )
        self.auth = make_sample_auth_context()

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T14:00:00+00:00")
    def test_finalizes_under_review_consultation(self, _mock_time, _mock_uuid) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation
        self.artifact_repo.get_artifact.return_value = None

        result = self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.status, ConsultationStatus.FINALIZED)

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T14:00:00+00:00")
    def test_stores_final_version_artifact(self, _mock_time, _mock_uuid) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation
        self.artifact_repo.get_artifact.return_value = None

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        # Find the save_artifact call for FINAL_VERSION
        final_version_calls = [
            c
            for c in self.artifact_repo.save_artifact.call_args_list
            if c[0][2] == ArtifactType.FINAL_VERSION
        ]
        self.assertEqual(len(final_version_calls), 1)
        final_data = final_version_calls[0][0][3]
        self.assertEqual(final_data["consultation_id"], "cons-001")
        self.assertEqual(final_data["finalized_at"], "2026-04-01T14:00:00+00:00")
        self.assertEqual(final_data["finalized_by"], "doc-001")

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T14:00:00+00:00")
    def test_transitions_to_finalized_status(self, _mock_time, _mock_uuid) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation
        self.artifact_repo.get_artifact.return_value = None

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        saved = self.consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.status, ConsultationStatus.FINALIZED)
        self.assertEqual(saved.finalized_at, "2026-04-01T14:00:00+00:00")
        self.assertEqual(saved.finalized_by, "doc-001")

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T14:00:00+00:00")
    def test_records_audit_event(self, _mock_time, _mock_uuid) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation
        self.artifact_repo.get_artifact.return_value = None

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.audit_repo.append.assert_called_once()
        audit_event = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit_event.event_type, AuditAction.CONSULTATION_FINALIZED)
        self.assertEqual(audit_event.actor_id, "doc-001")

    def test_idempotent_for_already_finalized(self) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-01T13:00:00+00:00",
            finalized_by="doc-001",
        )
        self.consultation_repo.find_by_id.return_value = consultation

        result = self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        # Should return existing consultation without re-saving
        self.assertEqual(result.status, ConsultationStatus.FINALIZED)
        self.consultation_repo.save.assert_not_called()
        self.audit_repo.append.assert_not_called()

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
            status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    def test_raises_finalization_not_allowed_for_draft_generated(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.DRAFT_GENERATED)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(FinalizationNotAllowedError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    def test_raises_finalization_not_allowed_for_in_processing(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.IN_PROCESSING)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(FinalizationNotAllowedError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T14:00:00+00:00")
    def test_uses_edited_artifacts_over_originals(self, _mock_time, _mock_uuid) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation

        edited_history = {"queixa_principal": {"descricao": "Edited"}}
        original_history = {"queixa_principal": {"descricao": "Original"}}

        def get_artifact_side_effect(clinic_id, consultation_id, artifact_type):
            if artifact_type == ArtifactType.PHYSICIAN_EDITS:
                return {"medical_history": edited_history}
            if artifact_type == ArtifactType.MEDICAL_HISTORY:
                return original_history
            if artifact_type == ArtifactType.SUMMARY:
                return {"subjetivo": {"queixa_principal": "Original summary"}}
            if artifact_type == ArtifactType.INSIGHTS:
                return {"observacoes": []}
            return None

        self.artifact_repo.get_artifact.side_effect = get_artifact_side_effect

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        # Find the FINAL_VERSION save
        final_calls = [
            c
            for c in self.artifact_repo.save_artifact.call_args_list
            if c[0][2] == ArtifactType.FINAL_VERSION
        ]
        self.assertEqual(len(final_calls), 1)
        final_data = final_calls[0][0][3]
        # Edited history should be used, not the original
        self.assertEqual(final_data["medical_history"], edited_history)


if __name__ == "__main__":
    unittest.main()
