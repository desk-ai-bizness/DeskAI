"""Unit tests for AI pipeline domain services."""

import unittest

from deskai.domain.ai_pipeline.services import ArtifactValidator, EvidenceLinker


class ArtifactValidatorAnamnesisTest(unittest.TestCase):
    def test_valid_anamnesis_returns_no_missing(self) -> None:
        data = {
            "queixa_principal": "dor de cabeca",
            "historia_doenca_atual": "paciente relata...",
            "historico_medico_pregresso": "hipertensao",
            "medicamentos_em_uso": "losartana",
            "alergias": "nenhuma",
            "revisao_de_sistemas": "sem alteracoes",
            "achados_exame_fisico": "PA 120/80",
            "observacoes_adicionais": "nenhuma",
            "campos_incompletos": [],
        }
        missing = ArtifactValidator.validate_anamnesis(data)
        self.assertEqual(missing, [])

    def test_missing_single_field(self) -> None:
        data = {
            "queixa_principal": "dor de cabeca",
            "historia_doenca_atual": "paciente relata...",
            "historico_medico_pregresso": "hipertensao",
            "medicamentos_em_uso": "losartana",
            "alergias": "nenhuma",
            "revisao_de_sistemas": "sem alteracoes",
            "achados_exame_fisico": "PA 120/80",
            "observacoes_adicionais": "nenhuma",
            # missing campos_incompletos
        }
        missing = ArtifactValidator.validate_anamnesis(data)
        self.assertEqual(missing, ["campos_incompletos"])

    def test_missing_multiple_fields(self) -> None:
        data = {
            "queixa_principal": "dor",
        }
        missing = ArtifactValidator.validate_anamnesis(data)
        self.assertEqual(len(missing), 8)
        self.assertIn("historia_doenca_atual", missing)
        self.assertIn("campos_incompletos", missing)

    def test_empty_dict_returns_all_fields(self) -> None:
        missing = ArtifactValidator.validate_anamnesis({})
        self.assertEqual(len(missing), 9)


class ArtifactValidatorSummaryTest(unittest.TestCase):
    def test_valid_summary_returns_no_missing(self) -> None:
        data = {
            "subjetivo": "paciente relata dor",
            "objetivo": "exame fisico normal",
            "avaliacao": "cefaleia tensional",
            "plano": "analgesia",
            "codigos_cid10_sugeridos": ["R51"],
            "aviso_revisao": "rascunho",
        }
        missing = ArtifactValidator.validate_summary(data)
        self.assertEqual(missing, [])

    def test_missing_fields(self) -> None:
        data = {
            "subjetivo": "dor",
            "objetivo": "normal",
        }
        missing = ArtifactValidator.validate_summary(data)
        self.assertEqual(len(missing), 4)
        self.assertIn("avaliacao", missing)
        self.assertIn("plano", missing)
        self.assertIn("codigos_cid10_sugeridos", missing)
        self.assertIn("aviso_revisao", missing)

    def test_empty_dict_returns_all_fields(self) -> None:
        missing = ArtifactValidator.validate_summary({})
        self.assertEqual(len(missing), 6)


class ArtifactValidatorInsightsTest(unittest.TestCase):
    def _valid_insights_data(self) -> dict:
        return {
            "observacoes": [
                {
                    "categoria": "lacuna_de_documentacao",
                    "descricao": "Falta informacao sobre alergias",
                    "severidade": "informativo",
                    "evidencia": {
                        "trecho": "nao mencionou alergias",
                        "contexto": "queixa principal",
                    },
                    "sugestao_revisao": "Revisar campo de alergias",
                }
            ],
            "resumo_observacoes": "1 observacao encontrada",
            "aviso_revisao": "rascunho",
        }

    def test_valid_insights_returns_no_missing(self) -> None:
        missing = ArtifactValidator.validate_insights(self._valid_insights_data())
        self.assertEqual(missing, [])

    def test_missing_required_fields(self) -> None:
        data = {"observacoes": []}
        missing = ArtifactValidator.validate_insights(data)
        self.assertIn("resumo_observacoes", missing)
        self.assertIn("aviso_revisao", missing)

    def test_empty_dict_returns_all_fields(self) -> None:
        missing = ArtifactValidator.validate_insights({})
        self.assertEqual(len(missing), 3)

    def test_invalid_category_detected(self) -> None:
        data = self._valid_insights_data()
        data["observacoes"][0]["categoria"] = "invalid_category"
        missing = ArtifactValidator.validate_insights(data)
        self.assertTrue(any("categoria" in m for m in missing))

    def test_missing_evidence_detected(self) -> None:
        data = self._valid_insights_data()
        del data["observacoes"][0]["evidencia"]
        missing = ArtifactValidator.validate_insights(data)
        self.assertTrue(any("evidencia" in m for m in missing))


class ArtifactValidatorInsightCategoriesTest(unittest.TestCase):
    def test_valid_categories(self) -> None:
        data = {
            "observacoes": [
                {"categoria": "lacuna_de_documentacao"},
                {"categoria": "inconsistencia"},
                {"categoria": "atencao_clinica"},
            ]
        }
        errors = ArtifactValidator.validate_insight_categories(data)
        self.assertEqual(errors, [])

    def test_invalid_category(self) -> None:
        data = {
            "observacoes": [
                {"categoria": "not_a_real_category"},
            ]
        }
        errors = ArtifactValidator.validate_insight_categories(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("categoria", errors[0])

    def test_empty_observacoes(self) -> None:
        data = {"observacoes": []}
        errors = ArtifactValidator.validate_insight_categories(data)
        self.assertEqual(errors, [])

    def test_missing_observacoes_key(self) -> None:
        errors = ArtifactValidator.validate_insight_categories({})
        self.assertEqual(errors, [])


class ArtifactValidatorInsightEvidenceTest(unittest.TestCase):
    def test_valid_evidence(self) -> None:
        data = {
            "observacoes": [
                {
                    "evidencia": {
                        "trecho": "dor de cabeca",
                        "contexto": "queixa",
                    }
                }
            ]
        }
        errors = ArtifactValidator.validate_insight_evidence(data)
        self.assertEqual(errors, [])

    def test_missing_evidence_key(self) -> None:
        data = {"observacoes": [{"descricao": "algo"}]}
        errors = ArtifactValidator.validate_insight_evidence(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("evidencia", errors[0])

    def test_missing_trecho_in_evidence(self) -> None:
        data = {"observacoes": [{"evidencia": {"contexto": "algo"}}]}
        errors = ArtifactValidator.validate_insight_evidence(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("trecho", errors[0])

    def test_missing_contexto_in_evidence(self) -> None:
        data = {"observacoes": [{"evidencia": {"trecho": "algo"}}]}
        errors = ArtifactValidator.validate_insight_evidence(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("contexto", errors[0])

    def test_empty_observacoes(self) -> None:
        errors = ArtifactValidator.validate_insight_evidence({"observacoes": []})
        self.assertEqual(errors, [])

    def test_missing_observacoes_key(self) -> None:
        errors = ArtifactValidator.validate_insight_evidence({})
        self.assertEqual(errors, [])


class EvidenceLinkerVerifyTest(unittest.TestCase):
    def test_all_evidence_found_in_transcript(self) -> None:
        transcript = "Paciente relata dor de cabeca forte desde ontem."
        data = {
            "observacoes": [
                {
                    "descricao": "dor",
                    "evidencia": {
                        "trecho": "dor de cabeca forte",
                        "contexto": "queixa",
                    },
                }
            ]
        }
        unverified = EvidenceLinker.verify_evidence_in_transcript(transcript, data)
        self.assertEqual(unverified, [])

    def test_evidence_not_found_flagged(self) -> None:
        transcript = "Paciente relata febre e tosse."
        data = {
            "observacoes": [
                {
                    "descricao": "dor",
                    "evidencia": {
                        "trecho": "dor de cabeca forte",
                        "contexto": "queixa",
                    },
                }
            ]
        }
        unverified = EvidenceLinker.verify_evidence_in_transcript(transcript, data)
        self.assertEqual(len(unverified), 1)
        self.assertEqual(unverified[0]["trecho"], "dor de cabeca forte")

    def test_case_insensitive_match(self) -> None:
        transcript = "PACIENTE RELATA DOR DE CABECA FORTE."
        data = {
            "observacoes": [
                {
                    "descricao": "dor",
                    "evidencia": {
                        "trecho": "dor de cabeca forte",
                        "contexto": "queixa",
                    },
                }
            ]
        }
        unverified = EvidenceLinker.verify_evidence_in_transcript(transcript, data)
        self.assertEqual(unverified, [])

    def test_empty_observacoes(self) -> None:
        unverified = EvidenceLinker.verify_evidence_in_transcript("transcript", {"observacoes": []})
        self.assertEqual(unverified, [])

    def test_missing_observacoes_key(self) -> None:
        unverified = EvidenceLinker.verify_evidence_in_transcript("transcript", {})
        self.assertEqual(unverified, [])

    def test_missing_evidencia_in_insight(self) -> None:
        data = {"observacoes": [{"descricao": "algo"}]}
        unverified = EvidenceLinker.verify_evidence_in_transcript("text", data)
        self.assertEqual(len(unverified), 1)

    def test_multiple_insights_mixed_results(self) -> None:
        transcript = "Paciente relata dor de cabeca e febre."
        data = {
            "observacoes": [
                {
                    "descricao": "dor",
                    "evidencia": {
                        "trecho": "dor de cabeca",
                        "contexto": "queixa",
                    },
                },
                {
                    "descricao": "nausea",
                    "evidencia": {
                        "trecho": "nausea persistente",
                        "contexto": "sintoma",
                    },
                },
            ]
        }
        unverified = EvidenceLinker.verify_evidence_in_transcript(transcript, data)
        self.assertEqual(len(unverified), 1)
        self.assertEqual(unverified[0]["trecho"], "nausea persistente")


class EvidenceLinkerCountByCategoryTest(unittest.TestCase):
    def test_counts_categories(self) -> None:
        data = {
            "observacoes": [
                {"categoria": "lacuna_de_documentacao"},
                {"categoria": "lacuna_de_documentacao"},
                {"categoria": "inconsistencia"},
            ]
        }
        counts = EvidenceLinker.count_by_category(data)
        self.assertEqual(counts["lacuna_de_documentacao"], 2)
        self.assertEqual(counts["inconsistencia"], 1)

    def test_empty_observacoes(self) -> None:
        counts = EvidenceLinker.count_by_category({"observacoes": []})
        self.assertEqual(counts, {})

    def test_missing_observacoes_key(self) -> None:
        counts = EvidenceLinker.count_by_category({})
        self.assertEqual(counts, {})


class EvidenceLinkerCountBySeverityTest(unittest.TestCase):
    def test_counts_severity(self) -> None:
        data = {
            "observacoes": [
                {"severidade": "informativo"},
                {"severidade": "importante"},
                {"severidade": "importante"},
            ]
        }
        counts = EvidenceLinker.count_by_severity(data)
        self.assertEqual(counts["informativo"], 1)
        self.assertEqual(counts["importante"], 2)

    def test_empty_observacoes(self) -> None:
        counts = EvidenceLinker.count_by_severity({"observacoes": []})
        self.assertEqual(counts, {})

    def test_missing_observacoes_key(self) -> None:
        counts = EvidenceLinker.count_by_severity({})
        self.assertEqual(counts, {})


if __name__ == "__main__":
    unittest.main()
