"""Unit tests for AI pipeline domain value objects."""

import unittest
from dataclasses import FrozenInstanceError

from deskai.domain.ai_pipeline.value_objects import (
    ArtifactResult,
    EvidenceExcerpt,
    GenerationMetadata,
    Insight,
    InsightCategory,
    InsightSeverity,
    StructuredOutput,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.shared.errors import DomainValidationError


class InsightCategoryTest(unittest.TestCase):
    def test_documentation_gap_value(self) -> None:
        self.assertEqual(InsightCategory.DOCUMENTATION_GAP, "lacuna_de_documentacao")

    def test_consistency_issue_value(self) -> None:
        self.assertEqual(InsightCategory.CONSISTENCY_ISSUE, "inconsistencia")

    def test_clinical_attention_value(self) -> None:
        self.assertEqual(InsightCategory.CLINICAL_ATTENTION, "atencao_clinica")

    def test_all_members(self) -> None:
        self.assertEqual(len(InsightCategory), 3)


class InsightSeverityTest(unittest.TestCase):
    def test_informative_value(self) -> None:
        self.assertEqual(InsightSeverity.INFORMATIVE, "informativo")

    def test_moderate_value(self) -> None:
        self.assertEqual(InsightSeverity.MODERATE, "moderado")

    def test_important_value(self) -> None:
        self.assertEqual(InsightSeverity.IMPORTANT, "importante")

    def test_all_members(self) -> None:
        self.assertEqual(len(InsightSeverity), 3)


class EvidenceExcerptTest(unittest.TestCase):
    def test_create_valid(self) -> None:
        ev = EvidenceExcerpt(trecho="dor de cabeca", contexto="queixa inicial")
        self.assertEqual(ev.trecho, "dor de cabeca")
        self.assertEqual(ev.contexto, "queixa inicial")

    def test_empty_trecho_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            EvidenceExcerpt(trecho="", contexto="some context")

    def test_whitespace_only_trecho_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            EvidenceExcerpt(trecho="   ", contexto="some context")

    def test_empty_contexto_allowed(self) -> None:
        ev = EvidenceExcerpt(trecho="febre alta", contexto="")
        self.assertEqual(ev.contexto, "")

    def test_frozen(self) -> None:
        ev = EvidenceExcerpt(trecho="dor", contexto="nota")
        with self.assertRaises(FrozenInstanceError):
            ev.trecho = "outra dor"


class InsightTest(unittest.TestCase):
    def _make_evidence(self) -> EvidenceExcerpt:
        return EvidenceExcerpt(trecho="dor no peito", contexto="queixa")

    def test_create_valid(self) -> None:
        ins = Insight(
            categoria=InsightCategory.CLINICAL_ATTENTION,
            descricao="Paciente relata dor no peito",
            severidade=InsightSeverity.IMPORTANT,
            evidencia=self._make_evidence(),
            sugestao_revisao="Revisar achados cardiovasculares",
        )
        self.assertEqual(ins.categoria, InsightCategory.CLINICAL_ATTENTION)
        self.assertEqual(ins.descricao, "Paciente relata dor no peito")
        self.assertEqual(ins.severidade, InsightSeverity.IMPORTANT)
        self.assertEqual(ins.evidencia.trecho, "dor no peito")
        self.assertEqual(ins.sugestao_revisao, "Revisar achados cardiovasculares")

    def test_empty_descricao_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            Insight(
                categoria=InsightCategory.DOCUMENTATION_GAP,
                descricao="",
                severidade=InsightSeverity.INFORMATIVE,
                evidencia=self._make_evidence(),
                sugestao_revisao="check",
            )

    def test_whitespace_descricao_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            Insight(
                categoria=InsightCategory.DOCUMENTATION_GAP,
                descricao="   ",
                severidade=InsightSeverity.INFORMATIVE,
                evidencia=self._make_evidence(),
                sugestao_revisao="check",
            )

    def test_frozen(self) -> None:
        ins = Insight(
            categoria=InsightCategory.CONSISTENCY_ISSUE,
            descricao="descricao valida",
            severidade=InsightSeverity.MODERATE,
            evidencia=self._make_evidence(),
            sugestao_revisao="revisar",
        )
        with self.assertRaises(FrozenInstanceError):
            ins.descricao = "outra"


class GenerationMetadataTest(unittest.TestCase):
    def test_create_valid(self) -> None:
        meta = GenerationMetadata(
            model_name="gpt-4o",
            prompt_version="v1.0",
            generation_timestamp="2026-04-03T10:00:00Z",
            duration_ms=1500,
            is_complete=True,
        )
        self.assertEqual(meta.model_name, "gpt-4o")
        self.assertEqual(meta.prompt_version, "v1.0")
        self.assertEqual(meta.generation_timestamp, "2026-04-03T10:00:00Z")
        self.assertEqual(meta.duration_ms, 1500)
        self.assertTrue(meta.is_complete)

    def test_empty_model_name_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            GenerationMetadata(
                model_name="",
                prompt_version="v1.0",
                generation_timestamp="2026-04-03T10:00:00Z",
                duration_ms=100,
                is_complete=True,
            )

    def test_whitespace_model_name_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            GenerationMetadata(
                model_name="   ",
                prompt_version="v1.0",
                generation_timestamp="2026-04-03T10:00:00Z",
                duration_ms=100,
                is_complete=True,
            )

    def test_negative_duration_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            GenerationMetadata(
                model_name="gpt-4o",
                prompt_version="v1.0",
                generation_timestamp="2026-04-03T10:00:00Z",
                duration_ms=-1,
                is_complete=True,
            )

    def test_zero_duration_allowed(self) -> None:
        meta = GenerationMetadata(
            model_name="gpt-4o",
            prompt_version="v1.0",
            generation_timestamp="2026-04-03T10:00:00Z",
            duration_ms=0,
            is_complete=False,
        )
        self.assertEqual(meta.duration_ms, 0)

    def test_frozen(self) -> None:
        meta = GenerationMetadata(
            model_name="gpt-4o",
            prompt_version="v1.0",
            generation_timestamp="2026-04-03T10:00:00Z",
            duration_ms=500,
            is_complete=True,
        )
        with self.assertRaises(FrozenInstanceError):
            meta.duration_ms = 999


class ArtifactResultTest(unittest.TestCase):
    def _make_metadata(self) -> GenerationMetadata:
        return GenerationMetadata(
            model_name="gpt-4o",
            prompt_version="v1.0",
            generation_timestamp="2026-04-03T10:00:00Z",
            duration_ms=500,
            is_complete=True,
        )

    def test_create_valid(self) -> None:
        ar = ArtifactResult(
            artifact_type=ArtifactType.MEDICAL_HISTORY,
            payload={"queixa_principal": "dor de cabeca"},
            metadata=self._make_metadata(),
        )
        self.assertEqual(ar.artifact_type, ArtifactType.MEDICAL_HISTORY)
        self.assertEqual(ar.payload, {"queixa_principal": "dor de cabeca"})
        self.assertTrue(ar.is_complete)

    def test_default_is_complete_true(self) -> None:
        ar = ArtifactResult(
            artifact_type=ArtifactType.SUMMARY,
            payload={},
            metadata=self._make_metadata(),
        )
        self.assertTrue(ar.is_complete)

    def test_explicit_is_complete_false(self) -> None:
        ar = ArtifactResult(
            artifact_type=ArtifactType.INSIGHTS,
            payload={},
            metadata=self._make_metadata(),
            is_complete=False,
        )
        self.assertFalse(ar.is_complete)

    def test_frozen(self) -> None:
        ar = ArtifactResult(
            artifact_type=ArtifactType.SUMMARY,
            payload={},
            metadata=self._make_metadata(),
        )
        with self.assertRaises(FrozenInstanceError):
            ar.is_complete = False


class StructuredOutputPreservedTest(unittest.TestCase):
    """Ensure existing StructuredOutput VO was not removed."""

    def test_structured_output_exists(self) -> None:
        so = StructuredOutput(task="anamnesis", payload={"key": "val"})
        self.assertEqual(so.task, "anamnesis")
        self.assertEqual(so.payload, {"key": "val"})


if __name__ == "__main__":
    unittest.main()
