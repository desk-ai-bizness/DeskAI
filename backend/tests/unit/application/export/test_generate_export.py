"""Unit tests for the GenerateExport use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.export.exceptions import ExportGenerationError
from deskai.domain.export.value_objects import ExportFormat, ExportResult
from deskai.domain.review.exceptions import ExportNotAllowedError
from tests.conftest import make_sample_auth_context, make_sample_consultation

_MOD = "deskai.application.export.generate_export"


class GenerateExportUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.artifact_repo = MagicMock()
        self.export_generator = MagicMock()
        self.storage_provider = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.export.generate_export import (
            GenerateExportUseCase,
        )

        self.use_case = GenerateExportUseCase(
            consultation_repo=self.consultation_repo,
            artifact_repo=self.artifact_repo,
            export_generator=self.export_generator,
            storage_provider=self.storage_provider,
            audit_repo=self.audit_repo,
        )
        self.auth = make_sample_auth_context()

        self.finalized_consultation = make_sample_consultation(
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-01T14:00:00+00:00",
            finalized_by="doc-001",
        )

        self.final_version = {
            "consultation_id": "cons-001",
            "medical_history": {"queixa_principal": {"descricao": "Headache"}},
            "summary": {"subjetivo": {"queixa_principal": "Headache"}},
            "accepted_insights": [],
        }

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T15:00:00+00:00")
    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    def test_generates_export_for_finalized_consultation(self, _mock_uuid, _mock_time) -> None:
        self.consultation_repo.find_by_id.return_value = self.finalized_consultation
        self.artifact_repo.get_artifact.return_value = self.final_version
        self.export_generator.generate.return_value = ExportResult(
            consultation_id="cons-001",
            format=ExportFormat.PDF,
            data=b"%PDF-fake-content",
            filename="final.pdf",
        )
        self.storage_provider.generate_presigned_url.return_value = (
            "https://s3.example.com/presigned"
        )

        result = self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.format, ExportFormat.PDF)

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T15:00:00+00:00")
    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    def test_returns_presigned_url(self, _mock_uuid, _mock_time) -> None:
        self.consultation_repo.find_by_id.return_value = self.finalized_consultation
        self.artifact_repo.get_artifact.return_value = self.final_version
        self.export_generator.generate.return_value = ExportResult(
            consultation_id="cons-001",
            format=ExportFormat.PDF,
            data=b"%PDF-fake",
            filename="final.pdf",
        )
        self.storage_provider.generate_presigned_url.return_value = (
            "https://s3.example.com/presigned-url"
        )

        result = self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.presigned_url, "https://s3.example.com/presigned-url")

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T15:00:00+00:00")
    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    def test_stores_pdf_in_s3(self, _mock_uuid, _mock_time) -> None:
        self.consultation_repo.find_by_id.return_value = self.finalized_consultation
        self.artifact_repo.get_artifact.return_value = self.final_version
        pdf_bytes = b"%PDF-content-here"
        self.export_generator.generate.return_value = ExportResult(
            consultation_id="cons-001",
            format=ExportFormat.PDF,
            data=pdf_bytes,
            filename="final.pdf",
        )
        self.storage_provider.generate_presigned_url.return_value = "url"

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.storage_provider.put.assert_called_once()
        put_args = self.storage_provider.put.call_args
        self.assertEqual(put_args[0][1], pdf_bytes)
        self.assertEqual(put_args[0][2], "application/pdf")

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T15:00:00+00:00")
    @patch(f"{_MOD}.new_uuid", return_value="evt-uuid-1")
    def test_records_audit_event(self, _mock_uuid, _mock_time) -> None:
        self.consultation_repo.find_by_id.return_value = self.finalized_consultation
        self.artifact_repo.get_artifact.return_value = self.final_version
        self.export_generator.generate.return_value = ExportResult(
            consultation_id="cons-001",
            format=ExportFormat.PDF,
            data=b"%PDF",
            filename="final.pdf",
        )
        self.storage_provider.generate_presigned_url.return_value = "url"

        self.use_case.execute(
            auth_context=self.auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.audit_repo.append.assert_called_once()
        audit_event = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit_event.event_type, AuditAction.EXPORT_GENERATED)
        self.assertEqual(audit_event.payload, {"format": "pdf"})

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
            status=ConsultationStatus.FINALIZED,
        )
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    def test_raises_export_not_allowed_for_non_finalized(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ExportNotAllowedError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    def test_raises_export_generation_error_when_final_version_missing(
        self,
    ) -> None:
        self.consultation_repo.find_by_id.return_value = self.finalized_consultation
        self.artifact_repo.get_artifact.return_value = None

        with self.assertRaises(ExportGenerationError):
            self.use_case.execute(
                auth_context=self.auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )


if __name__ == "__main__":
    unittest.main()
