"""Tests for PdfExportGenerator adapter."""

import unittest

from deskai.adapters.export.pdf_generator import PdfExportGenerator
from deskai.domain.export.value_objects import ExportFormat


class PdfExportGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.generator = PdfExportGenerator()
        self.metadata = {
            "scheduled_date": "2026-04-01",
            "specialty": "general_practice",
            "finalized_at": "2026-04-01T12:00:00+00:00",
        }
        self.medical_history = {
            "queixa_principal": {"descricao": "Dor de cabeca"},
        }
        self.summary = {
            "subjetivo": {"queixa_principal": "Cefaleia"},
        }
        self.insights = [
            {
                "categoria": "lacuna_de_documentacao",
                "descricao": "Exame fisico ausente",
                "severidade": "moderado",
                "evidencia": {"trecho": "Dor ha dois dias", "contexto": "Relato"},
            }
        ]

    def test_generate_returns_export_result(self):
        result = self.generator.generate(
            "cons-001",
            ExportFormat.PDF,
            self.metadata,
            self.medical_history,
            self.summary,
            self.insights,
        )
        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.format, ExportFormat.PDF)
        self.assertIsInstance(result.data, bytes)
        self.assertGreater(len(result.data), 0)

    def test_generate_returns_pdf_starting_with_header(self):
        result = self.generator.generate(
            "cons-001",
            ExportFormat.PDF,
            self.metadata,
            self.medical_history,
            self.summary,
            self.insights,
        )
        self.assertTrue(result.data.startswith(b"%PDF-1.4"))

    def test_generate_includes_consultation_id_in_filename(self):
        result = self.generator.generate(
            "cons-abc",
            ExportFormat.PDF,
            self.metadata,
            self.medical_history,
            self.summary,
            self.insights,
        )
        self.assertIn("cons-abc", result.filename)

    def test_generate_with_empty_insights(self):
        result = self.generator.generate(
            "cons-001",
            ExportFormat.PDF,
            self.metadata,
            self.medical_history,
            self.summary,
            [],
        )
        self.assertIsInstance(result.data, bytes)
        self.assertGreater(len(result.data), 0)

    def test_generate_with_empty_medical_history(self):
        result = self.generator.generate(
            "cons-001",
            ExportFormat.PDF,
            self.metadata,
            {},
            self.summary,
            [],
        )
        self.assertIsInstance(result.data, bytes)

    def test_generate_with_special_characters(self):
        history = {"nota": "Paciente relata (dor) forte \\ intensa"}
        result = self.generator.generate(
            "cons-001",
            ExportFormat.PDF,
            self.metadata,
            history,
            self.summary,
            [],
        )
        self.assertTrue(result.data.startswith(b"%PDF-1.4"))

    def test_generate_with_nested_dict(self):
        history = {
            "section_a": {
                "subsection": {"key": "value"},
                "list_field": ["item1", "item2"],
            }
        }
        result = self.generator.generate(
            "cons-001",
            ExportFormat.PDF,
            self.metadata,
            history,
            {},
            [],
        )
        self.assertIsInstance(result.data, bytes)


if __name__ == "__main__":
    unittest.main()
