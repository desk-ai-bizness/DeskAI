"""Unit tests for the export domain layer."""

import unittest

from deskai.domain.export.entities import ExportArtifact, ExportRequest
from deskai.domain.export.exceptions import ExportGenerationError
from deskai.domain.export.services import (
    build_edits_s3_key,
    build_export_s3_key,
    build_final_version_s3_key,
)
from deskai.domain.export.value_objects import ExportFormat, ExportResult
from deskai.shared.errors import DeskAIError, DomainValidationError

# =========================================================================
# ExportFormat enum
# =========================================================================


class TestExportFormat(unittest.TestCase):
    def test_pdf_value(self):
        self.assertEqual(ExportFormat.PDF.value, "pdf")

    def test_pdf_is_string(self):
        self.assertIsInstance(ExportFormat.PDF, str)


# =========================================================================
# ExportResult value object
# =========================================================================


class TestExportResult(unittest.TestCase):
    def test_fields(self):
        result = ExportResult(
            consultation_id="c-1",
            format=ExportFormat.PDF,
            data=b"fake-pdf",
            filename="test.pdf",
        )
        self.assertEqual(result.consultation_id, "c-1")
        self.assertEqual(result.format, ExportFormat.PDF)
        self.assertEqual(result.data, b"fake-pdf")
        self.assertEqual(result.filename, "test.pdf")

    def test_is_frozen(self):
        result = ExportResult(
            consultation_id="c-1",
            format=ExportFormat.PDF,
            data=b"data",
            filename="f.pdf",
        )
        with self.assertRaises(AttributeError):
            result.filename = "other.pdf"


# =========================================================================
# ExportRequest entity validation
# =========================================================================


class TestExportRequestValidation(unittest.TestCase):
    def _make(self, **overrides):
        defaults = dict(
            consultation_id="c-1",
            clinic_id="cl-1",
            doctor_id="d-1",
            format=ExportFormat.PDF,
        )
        defaults.update(overrides)
        return ExportRequest(**defaults)

    def test_valid_request(self):
        req = self._make()
        self.assertEqual(req.consultation_id, "c-1")
        self.assertEqual(req.clinic_id, "cl-1")
        self.assertEqual(req.doctor_id, "d-1")
        self.assertEqual(req.format, ExportFormat.PDF)

    def test_default_format_is_pdf(self):
        req = ExportRequest(consultation_id="c-1", clinic_id="cl-1", doctor_id="d-1")
        self.assertEqual(req.format, ExportFormat.PDF)

    def test_empty_consultation_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="")

    def test_whitespace_consultation_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="   ")

    def test_empty_clinic_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="")

    def test_whitespace_clinic_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(clinic_id="  ")

    def test_empty_doctor_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(doctor_id="")

    def test_whitespace_doctor_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(doctor_id="  ")

    def test_is_frozen(self):
        req = self._make()
        with self.assertRaises(AttributeError):
            req.consultation_id = "other"


# =========================================================================
# ExportArtifact entity validation
# =========================================================================


class TestExportArtifactValidation(unittest.TestCase):
    def _make(self, **overrides):
        defaults = dict(
            consultation_id="c-1",
            format=ExportFormat.PDF,
            storage_key="clinics/cl-1/consultations/c-1/exports/final.pdf",
            presigned_url="https://s3.example.com/file",
            expires_at="2026-04-03T12:00:00Z",
        )
        defaults.update(overrides)
        return ExportArtifact(**defaults)

    def test_valid_artifact(self):
        art = self._make()
        self.assertEqual(art.consultation_id, "c-1")
        self.assertEqual(art.format, ExportFormat.PDF)
        self.assertIn("final.pdf", art.storage_key)

    def test_empty_consultation_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="")

    def test_whitespace_consultation_id_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(consultation_id="   ")

    def test_empty_storage_key_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(storage_key="")

    def test_whitespace_storage_key_raises(self):
        with self.assertRaises(DomainValidationError):
            self._make(storage_key="   ")

    def test_is_frozen(self):
        art = self._make()
        with self.assertRaises(AttributeError):
            art.storage_key = "changed"


# =========================================================================
# ExportGenerationError exception
# =========================================================================


class TestExportGenerationError(unittest.TestCase):
    def test_inherits_deskai_error(self):
        err = ExportGenerationError("c-1", "timeout")
        self.assertIsInstance(err, DeskAIError)

    def test_message_includes_consultation_id(self):
        err = ExportGenerationError("c-42", "disk full")
        self.assertIn("c-42", str(err))
        self.assertIn("disk full", str(err))

    def test_attributes(self):
        err = ExportGenerationError("c-1", "reason-text")
        self.assertEqual(err.consultation_id, "c-1")
        self.assertEqual(err.reason, "reason-text")


# =========================================================================
# Export domain services (S3 key builders)
# =========================================================================


class TestBuildExportS3Key(unittest.TestCase):
    def test_pattern(self):
        key = build_export_s3_key("cl-1", "c-1")
        self.assertEqual(key, "clinics/cl-1/consultations/c-1/exports/final.pdf")

    def test_different_ids(self):
        key = build_export_s3_key("clinic-abc", "consult-xyz")
        self.assertEqual(
            key,
            "clinics/clinic-abc/consultations/consult-xyz/exports/final.pdf",
        )


class TestBuildFinalVersionS3Key(unittest.TestCase):
    def test_pattern(self):
        key = build_final_version_s3_key("cl-1", "c-1")
        self.assertEqual(key, "clinics/cl-1/consultations/c-1/review/final.json")


class TestBuildEditsS3Key(unittest.TestCase):
    def test_pattern(self):
        key = build_edits_s3_key("cl-1", "c-1")
        self.assertEqual(key, "clinics/cl-1/consultations/c-1/review/edits.json")


# =========================================================================
# PdfExportGenerator adapter
# =========================================================================


class TestPdfExportGenerator(unittest.TestCase):
    def _make_generator(self):
        from deskai.adapters.export.pdf_generator import PdfExportGenerator

        return PdfExportGenerator()

    def _sample_metadata(self):
        return {
            "scheduled_date": "2026-04-01",
            "specialty": "general",
            "doctor_id": "d-1",
            "patient_id": "p-1",
            "finalized_at": "2026-04-01T18:00:00Z",
        }

    def _sample_medical_history(self):
        return {
            "queixa_principal": "Dor de cabeca persistente",
            "historia_doenca_atual": "Paciente relata cefaleia ha 3 dias",
            "antecedentes": {"pessoais": "Hipertensao", "familiares": "DM"},
        }

    def _sample_summary(self):
        return {
            "subjetivo": "Paciente relata dor de cabeca ha 3 dias",
            "objetivo": "PA 140/90, FC 80bpm",
            "avaliacao": "Cefaleia tensional",
            "plano": "Prescrito analgesico, retorno em 7 dias",
        }

    def _sample_insights(self):
        return [
            {
                "descricao": "Verificar historico de enxaqueca",
                "categoria": "atencao_clinica",
                "severidade": "media",
                "evidencia": {
                    "trecho": "Paciente menciona dores frequentes",
                },
            },
        ]

    def test_generate_returns_export_result(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-1",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history=self._sample_medical_history(),
            summary=self._sample_summary(),
            accepted_insights=self._sample_insights(),
        )
        self.assertIsInstance(result, ExportResult)

    def test_generate_returns_non_empty_bytes(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-1",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history=self._sample_medical_history(),
            summary=self._sample_summary(),
            accepted_insights=self._sample_insights(),
        )
        self.assertGreater(len(result.data), 0)

    def test_generate_returns_valid_pdf_header(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-1",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history=self._sample_medical_history(),
            summary=self._sample_summary(),
            accepted_insights=self._sample_insights(),
        )
        self.assertTrue(result.data.startswith(b"%PDF"))

    def test_generate_filename_includes_consultation_id(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-42",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history=self._sample_medical_history(),
            summary=self._sample_summary(),
            accepted_insights=self._sample_insights(),
        )
        self.assertIn("c-42", result.filename)

    def test_generate_with_empty_insights(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-1",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history=self._sample_medical_history(),
            summary=self._sample_summary(),
            accepted_insights=[],
        )
        self.assertIsInstance(result, ExportResult)
        self.assertTrue(result.data.startswith(b"%PDF"))

    def test_generate_with_empty_medical_history(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-1",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history={},
            summary=self._sample_summary(),
            accepted_insights=self._sample_insights(),
        )
        self.assertIsInstance(result, ExportResult)
        self.assertTrue(result.data.startswith(b"%PDF"))

    def test_generate_with_empty_summary(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-1",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history=self._sample_medical_history(),
            summary={},
            accepted_insights=self._sample_insights(),
        )
        self.assertIsInstance(result, ExportResult)
        self.assertTrue(result.data.startswith(b"%PDF"))

    def test_generate_result_format_matches_input(self):
        gen = self._make_generator()
        result = gen.generate(
            consultation_id="c-1",
            fmt=ExportFormat.PDF,
            metadata=self._sample_metadata(),
            medical_history=self._sample_medical_history(),
            summary=self._sample_summary(),
            accepted_insights=self._sample_insights(),
        )
        self.assertEqual(result.format, ExportFormat.PDF)
        self.assertEqual(result.consultation_id, "c-1")


# =========================================================================
# StubExportGenerator adapter
# =========================================================================


class TestStubExportGenerator(unittest.TestCase):
    def test_raises_not_implemented(self):
        from deskai.adapters.export.stub_generator import StubExportGenerator

        gen = StubExportGenerator()
        with self.assertRaises(NotImplementedError):
            gen.generate(
                consultation_id="c-1",
                fmt=ExportFormat.PDF,
                metadata={},
                medical_history={},
                summary={},
                accepted_insights=[],
            )


if __name__ == "__main__":
    unittest.main()
