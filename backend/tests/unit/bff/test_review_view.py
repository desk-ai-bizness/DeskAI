"""Tests for BFF review, finalize, and export view builders."""

import unittest

from deskai.bff.views.review_view import (
    build_export_view,
    build_finalize_view,
    build_review_view,
)
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.export.entities import ExportArtifact
from deskai.domain.export.value_objects import ExportFormat
from deskai.domain.review.entities import ReviewPayload


class BuildReviewViewTest(unittest.TestCase):
    def _make_payload(self, **overrides):
        defaults = dict(
            consultation_id="cons-001",
            medical_history={"queixa_principal": {"descricao": "Dor"}},
            summary={"subjetivo": {"queixa_principal": "Dor"}},
            insights=[],
        )
        defaults.update(overrides)
        return ReviewPayload(**defaults)

    def test_returns_correct_structure(self):
        payload = self._make_payload()
        view = build_review_view(payload)
        self.assertEqual(view["consultation_id"], "cons-001")
        self.assertEqual(view["status"], "under_physician_review")
        self.assertIn("medical_history", view)
        self.assertIn("summary", view)
        self.assertIn("insights", view)

    def test_medical_history_includes_content_and_flags(self):
        payload = self._make_payload(medical_history_edited=True)
        view = build_review_view(payload)
        self.assertEqual(
            view["medical_history"]["content"],
            {"queixa_principal": {"descricao": "Dor"}},
        )
        self.assertTrue(view["medical_history"]["edited_by_physician"])

    def test_summary_includes_content_and_flags(self):
        payload = self._make_payload(summary_edited=True)
        view = build_review_view(payload)
        self.assertTrue(view["summary"]["edited_by_physician"])

    def test_completeness_warning_propagated(self):
        payload = self._make_payload(completeness_warning=True)
        view = build_review_view(payload)
        self.assertTrue(view["medical_history"]["completeness_warning"])
        self.assertTrue(view["summary"]["completeness_warning"])

    def test_insights_mapped_correctly(self):
        insights = [
            {
                "categoria": "lacuna_de_documentacao",
                "descricao": "Exame fisico ausente",
                "severidade": "moderado",
                "evidencia": {
                    "trecho": "Dor ha dois dias",
                    "contexto": "Paciente relata",
                },
                "sugestao_revisao": "Registrar",
            }
        ]
        payload = self._make_payload(insights=insights)
        view = build_review_view(payload)
        self.assertEqual(len(view["insights"]), 1)
        insight = view["insights"][0]
        self.assertEqual(insight["insight_id"], "0")
        self.assertEqual(insight["category"], "lacuna_de_documentacao")
        self.assertEqual(insight["description"], "Exame fisico ausente")
        self.assertEqual(insight["status"], "pending")
        self.assertEqual(len(insight["evidence"]), 1)

    def test_empty_insights_returns_empty_list(self):
        payload = self._make_payload(insights=[])
        view = build_review_view(payload)
        self.assertEqual(view["insights"], [])

    def test_ui_config_included_when_provided(self):
        payload = self._make_payload()
        config = {"labels": {"title": "Revisao"}}
        view = build_review_view(payload, ui_config=config)
        self.assertEqual(view["ui_config"], config)

    def test_ui_config_absent_when_not_provided(self):
        payload = self._make_payload()
        view = build_review_view(payload)
        self.assertNotIn("ui_config", view)

    def test_with_edited_flags_both_true(self):
        payload = self._make_payload(
            medical_history_edited=True,
            summary_edited=True,
        )
        view = build_review_view(payload)
        self.assertTrue(view["medical_history"]["edited_by_physician"])
        self.assertTrue(view["summary"]["edited_by_physician"])

    def test_none_insights_returns_empty_list(self):
        payload = self._make_payload(insights=None)
        view = build_review_view(payload)
        self.assertEqual(view["insights"], [])

    def test_insight_without_evidence_produces_empty_list(self):
        insights = [
            {
                "categoria": "inconsistencia",
                "descricao": "Dados conflitantes",
                "severidade": "informativo",
            },
        ]
        payload = self._make_payload(insights=insights)
        view = build_review_view(payload)
        self.assertEqual(len(view["insights"]), 1)
        self.assertEqual(view["insights"][0]["evidence"], [])

    def test_multiple_insights_numbered_sequentially(self):
        insights = [
            {"categoria": "a", "descricao": "First", "severidade": "info"},
            {"categoria": "b", "descricao": "Second", "severidade": "mod"},
            {"categoria": "c", "descricao": "Third", "severidade": "imp"},
        ]
        payload = self._make_payload(insights=insights)
        view = build_review_view(payload)
        ids = [i["insight_id"] for i in view["insights"]]
        self.assertEqual(ids, ["0", "1", "2"])


class BuildFinalizeViewTest(unittest.TestCase):
    def test_returns_correct_structure(self):
        consultation = Consultation(
            consultation_id="cons-001",
            clinic_id="clinic-001",
            doctor_id="doc-001",
            patient_id="pat-001",
            specialty="general_practice",
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-04T10:00:00+00:00",
            finalized_by="doc-001",
        )
        view = build_finalize_view(consultation)
        self.assertEqual(view["consultation_id"], "cons-001")
        self.assertEqual(view["status"], "finalized")
        self.assertEqual(view["finalized_at"], "2026-04-04T10:00:00+00:00")
        self.assertEqual(view["finalized_by"], "doc-001")

    def test_non_finalized_consultation(self):
        consultation = Consultation(
            consultation_id="cons-002",
            clinic_id="clinic-001",
            doctor_id="doc-001",
            patient_id="pat-001",
            specialty="general_practice",
            status=ConsultationStatus.STARTED,
        )
        view = build_finalize_view(consultation)
        self.assertEqual(view["status"], "started")
        self.assertIsNone(view["finalized_at"])
        self.assertIsNone(view["finalized_by"])


class BuildExportViewTest(unittest.TestCase):
    def test_returns_correct_structure(self):
        artifact = ExportArtifact(
            consultation_id="cons-001",
            format=ExportFormat.PDF,
            storage_key="clinics/c/consultations/cons-001/exports/final.pdf",
            presigned_url="https://s3.example.com/signed",
            expires_at="2026-04-04T11:00:00+00:00",
        )
        view = build_export_view(artifact)
        self.assertEqual(view["consultation_id"], "cons-001")
        self.assertEqual(view["export_url"], "https://s3.example.com/signed")
        self.assertEqual(view["expires_at"], "2026-04-04T11:00:00+00:00")
        self.assertEqual(view["format"], "pdf")

    def test_includes_presigned_url(self):
        artifact = ExportArtifact(
            consultation_id="cons-002",
            format=ExportFormat.PDF,
            storage_key="key",
            presigned_url="https://bucket.s3.amazonaws.com/key?token=abc",
            expires_at="2026-04-04T12:00:00+00:00",
        )
        view = build_export_view(artifact)
        self.assertIn("token=abc", view["export_url"])


if __name__ == "__main__":
    unittest.main()
