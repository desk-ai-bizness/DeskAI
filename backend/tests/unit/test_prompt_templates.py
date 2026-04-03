"""Tests for production prompt templates -- structural and rendering validation."""

import re

import pytest

from deskai.prompts.anamnesis_prompt import (
    ANAMNESIS_SYSTEM_PROMPT,
    ANAMNESIS_USER_TEMPLATE,
)
from deskai.prompts.insights_prompt import (
    INSIGHTS_SYSTEM_PROMPT,
    INSIGHTS_USER_TEMPLATE,
)
from deskai.prompts.prescription_prompt import (
    PRESCRIPTION_SYSTEM_PROMPT,
    PRESCRIPTION_USER_TEMPLATE,
)
from deskai.prompts.summary_prompt import (
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_TEMPLATE,
)
from deskai.prompts.transcript_prompt import (
    TRANSCRIPT_SYSTEM_PROMPT,
    TRANSCRIPT_USER_TEMPLATE,
)
from deskai.prompts.prompt_loader import render_prompt

# Regex to find Python str.format-style template variables like {name}.
_FORMAT_VAR_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}", re.IGNORECASE)

# Known JSON schema field names used inside system prompt examples (not template vars).
_SCHEMA_FIELD_NAMES = frozenset({
    "queixa_principal", "descricao", "duracao", "historia_doenca_atual",
    "narrativa", "sintomas", "nome", "inicio", "intensidade",
    "fatores_agravantes", "fatores_atenuantes", "localizacao",
    "historico_medico_pregresso", "doencas_previas", "cirurgias_previas",
    "internacoes_previas", "medicamentos_em_uso", "dose", "frequencia",
    "alergias", "relatadas", "nega_alergias", "revisao_de_sistemas",
    "sistemas_mencionados", "sistema", "achados", "sistemas_nao_avaliados",
    "achados_exame_fisico", "regiao_ou_sistema", "achado", "valor",
    "observacoes_adicionais", "campos_incompletos",
    "medicamentos", "nome_generico", "nome_comercial", "concentracao",
    "forma_farmaceutica", "via_administracao", "instrucoes_adicionais",
    "alertas", "tipo", "severidade", "orientacoes_gerais", "retorno",
    "alertas_globais", "aviso_revisao",
    "subjetivo", "historia", "informacoes_adicionais", "objetivo",
    "exame_fisico", "sinais_vitais", "pressao_arterial",
    "frequencia_cardiaca", "temperatura", "saturacao_o2", "outros",
    "exames_complementares", "avaliacao", "hipoteses_diagnosticas",
    "cid10_sugerido", "confianca", "observacoes", "plano", "condutas",
    "exames_solicitados", "encaminhamentos", "prescricoes_mencionadas",
    "orientacoes_ao_paciente", "codigos_cid10_sugeridos", "codigo",
    "justificativa",
    "segmentos", "falante", "texto", "timestamp_inicio", "timestamp_fim",
    "metadados", "total_segmentos", "falantes_identificados",
    "duracao_estimada", "idioma", "correcoes_aplicadas", "original",
    "corrigido", "motivo",
    "categoria", "evidencia", "trecho", "contexto", "sugestao_revisao",
    "resumo_observacoes", "total", "por_categoria",
    "lacuna_de_documentacao", "inconsistencia", "atencao_clinica",
    "por_severidade", "informativo", "moderado", "importante",
    "key", "value",
})


def _find_template_variables(text: str) -> list[str]:
    """Find Python format-string variables that are NOT JSON schema fields."""
    matches = _FORMAT_VAR_RE.findall(text)
    return [m for m in matches if m not in _SCHEMA_FIELD_NAMES]


# -------------------------------------------------------------------------
# Prompt structural validations
# -------------------------------------------------------------------------


class TestAnamnesisPrompt:
    """Tests for the anamnesis prompt template."""

    def test_system_prompt_is_not_empty(self) -> None:
        assert len(ANAMNESIS_SYSTEM_PROMPT) > 500

    def test_system_prompt_contains_output_schema(self) -> None:
        assert "ESQUEMA DE SAIDA" in ANAMNESIS_SYSTEM_PROMPT

    def test_system_prompt_contains_no_fabrication_rule(self) -> None:
        assert "Nao invente" in ANAMNESIS_SYSTEM_PROMPT

    def test_system_prompt_requires_json(self) -> None:
        assert "JSON" in ANAMNESIS_SYSTEM_PROMPT

    def test_system_prompt_contains_key_fields(self) -> None:
        assert "queixa_principal" in ANAMNESIS_SYSTEM_PROMPT
        assert "historia_doenca_atual" in ANAMNESIS_SYSTEM_PROMPT
        assert "historico_medico_pregresso" in ANAMNESIS_SYSTEM_PROMPT
        assert "medicamentos_em_uso" in ANAMNESIS_SYSTEM_PROMPT
        assert "alergias" in ANAMNESIS_SYSTEM_PROMPT
        assert "revisao_de_sistemas" in ANAMNESIS_SYSTEM_PROMPT
        assert "achados_exame_fisico" in ANAMNESIS_SYSTEM_PROMPT
        assert "campos_incompletos" in ANAMNESIS_SYSTEM_PROMPT

    def test_system_prompt_has_no_template_variables(self) -> None:
        assert _find_template_variables(ANAMNESIS_SYSTEM_PROMPT) == []

    def test_user_template_has_required_variables(self) -> None:
        assert "{transcript}" in ANAMNESIS_USER_TEMPLATE
        assert "{patient_name}" in ANAMNESIS_USER_TEMPLATE
        assert "{patient_dob}" in ANAMNESIS_USER_TEMPLATE
        assert "{consultation_date}" in ANAMNESIS_USER_TEMPLATE

    def test_user_template_renders_successfully(self) -> None:
        result = render_prompt(ANAMNESIS_USER_TEMPLATE, {
            "transcript": "Medico: Qual a queixa? Paciente: Dor de cabeca.",
            "patient_name": "Joao Silva",
            "patient_dob": "1990-05-15",
            "consultation_date": "2026-04-01",
        })
        assert "Joao Silva" in result
        assert "Dor de cabeca" in result


class TestPrescriptionPrompt:
    """Tests for the prescription prompt template."""

    def test_system_prompt_is_not_empty(self) -> None:
        assert len(PRESCRIPTION_SYSTEM_PROMPT) > 500

    def test_system_prompt_contains_safety_alerts(self) -> None:
        assert "ALERTAS DE SEGURANCA" in PRESCRIPTION_SYSTEM_PROMPT

    def test_system_prompt_contains_drug_interaction_check(self) -> None:
        assert "interacao" in PRESCRIPTION_SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_dosage_check(self) -> None:
        assert "dose" in PRESCRIPTION_SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_allergy_check(self) -> None:
        assert "alergia" in PRESCRIPTION_SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_review_warning(self) -> None:
        assert "aviso_revisao" in PRESCRIPTION_SYSTEM_PROMPT

    def test_system_prompt_has_no_template_variables(self) -> None:
        assert _find_template_variables(PRESCRIPTION_SYSTEM_PROMPT) == []

    def test_user_template_has_required_variables(self) -> None:
        assert "{consultation_data}" in PRESCRIPTION_USER_TEMPLATE
        assert "{allergies}" in PRESCRIPTION_USER_TEMPLATE
        assert "{current_medications}" in PRESCRIPTION_USER_TEMPLATE
        assert "{patient_name}" in PRESCRIPTION_USER_TEMPLATE

    def test_user_template_renders_successfully(self) -> None:
        result = render_prompt(PRESCRIPTION_USER_TEMPLATE, {
            "consultation_data": "Medico prescreveu amoxicilina 500mg.",
            "allergies": "Nenhuma relatada.",
            "current_medications": "Nenhum.",
            "patient_name": "Maria Santos",
            "patient_dob": "1985-03-20",
            "consultation_date": "2026-04-01",
        })
        assert "Maria Santos" in result
        assert "amoxicilina" in result


class TestSummaryPrompt:
    """Tests for the summary (SOAP) prompt template."""

    def test_system_prompt_is_not_empty(self) -> None:
        assert len(SUMMARY_SYSTEM_PROMPT) > 500

    def test_system_prompt_contains_soap_format(self) -> None:
        assert "SOAP" in SUMMARY_SYSTEM_PROMPT

    def test_system_prompt_contains_soap_sections(self) -> None:
        assert "Subjetivo" in SUMMARY_SYSTEM_PROMPT
        assert "Objetivo" in SUMMARY_SYSTEM_PROMPT
        assert "Avaliacao" in SUMMARY_SYSTEM_PROMPT
        assert "Plano" in SUMMARY_SYSTEM_PROMPT

    def test_system_prompt_contains_cid10(self) -> None:
        assert "CID-10" in SUMMARY_SYSTEM_PROMPT

    def test_system_prompt_contains_review_warning(self) -> None:
        assert "aviso_revisao" in SUMMARY_SYSTEM_PROMPT

    def test_system_prompt_has_no_template_variables(self) -> None:
        assert _find_template_variables(SUMMARY_SYSTEM_PROMPT) == []

    def test_user_template_has_required_variables(self) -> None:
        assert "{transcript}" in SUMMARY_USER_TEMPLATE
        assert "{anamnesis_json}" in SUMMARY_USER_TEMPLATE
        assert "{patient_name}" in SUMMARY_USER_TEMPLATE
        assert "{specialty}" in SUMMARY_USER_TEMPLATE

    def test_user_template_renders_successfully(self) -> None:
        result = render_prompt(SUMMARY_USER_TEMPLATE, {
            "transcript": "Medico: Boa tarde.",
            "anamnesis_json": '{"queixa_principal": "dor"}',
            "patient_name": "Carlos Lima",
            "patient_dob": "1975-11-10",
            "consultation_date": "2026-04-01",
            "specialty": "clinica_geral",
        })
        assert "Carlos Lima" in result


class TestTranscriptPrompt:
    """Tests for the transcript normalization prompt template."""

    def test_system_prompt_is_not_empty(self) -> None:
        assert len(TRANSCRIPT_SYSTEM_PROMPT) > 500

    def test_system_prompt_contains_normalization_rules(self) -> None:
        assert "NORMALIZACAO PERMITIDA" in TRANSCRIPT_SYSTEM_PROMPT
        assert "NORMALIZACAO PROIBIDA" in TRANSCRIPT_SYSTEM_PROMPT

    def test_system_prompt_contains_speaker_labels(self) -> None:
        assert "medico" in TRANSCRIPT_SYSTEM_PROMPT
        assert "paciente" in TRANSCRIPT_SYSTEM_PROMPT

    def test_system_prompt_preserves_content_rule(self) -> None:
        assert "Preserve o conteudo original" in TRANSCRIPT_SYSTEM_PROMPT

    def test_system_prompt_has_no_template_variables(self) -> None:
        assert _find_template_variables(TRANSCRIPT_SYSTEM_PROMPT) == []

    def test_user_template_has_required_variables(self) -> None:
        assert "{raw_transcript}" in TRANSCRIPT_USER_TEMPLATE
        assert "{consultation_id}" in TRANSCRIPT_USER_TEMPLATE
        assert "{consultation_date}" in TRANSCRIPT_USER_TEMPLATE
        assert "{provider_name}" in TRANSCRIPT_USER_TEMPLATE

    def test_user_template_renders_successfully(self) -> None:
        result = render_prompt(TRANSCRIPT_USER_TEMPLATE, {
            "raw_transcript": "00:00 Speaker 1: Boa tarde.",
            "consultation_id": "cons-001",
            "consultation_date": "2026-04-01",
            "provider_name": "elevenlabs",
        })
        assert "cons-001" in result
        assert "Boa tarde" in result


class TestInsightsPrompt:
    """Tests for the insights prompt template."""

    def test_system_prompt_is_not_empty(self) -> None:
        assert len(INSIGHTS_SYSTEM_PROMPT) > 500

    def test_system_prompt_contains_allowed_categories(self) -> None:
        assert "lacuna_de_documentacao" in INSIGHTS_SYSTEM_PROMPT
        assert "inconsistencia" in INSIGHTS_SYSTEM_PROMPT
        assert "atencao_clinica" in INSIGHTS_SYSTEM_PROMPT

    def test_system_prompt_requires_evidence(self) -> None:
        assert "evidencia" in INSIGHTS_SYSTEM_PROMPT

    def test_system_prompt_contains_no_diagnosis_rule(self) -> None:
        assert "diagnostico" in INSIGHTS_SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_review_warning(self) -> None:
        assert "aviso_revisao" in INSIGHTS_SYSTEM_PROMPT

    def test_system_prompt_has_no_template_variables(self) -> None:
        assert _find_template_variables(INSIGHTS_SYSTEM_PROMPT) == []

    def test_user_template_has_required_variables(self) -> None:
        assert "{transcript}" in INSIGHTS_USER_TEMPLATE
        assert "{anamnesis_json}" in INSIGHTS_USER_TEMPLATE
        assert "{summary_json}" in INSIGHTS_USER_TEMPLATE
        assert "{patient_name}" in INSIGHTS_USER_TEMPLATE

    def test_user_template_renders_successfully(self) -> None:
        result = render_prompt(INSIGHTS_USER_TEMPLATE, {
            "transcript": "Medico: Alguma alergia? Paciente: Nao sei.",
            "anamnesis_json": '{"alergias": "revisao_necessaria"}',
            "summary_json": '{"subjetivo": {"queixa_principal": "dor"}}',
            "patient_name": "Ana Pereira",
            "patient_dob": "2000-01-01",
            "consultation_date": "2026-04-01",
        })
        assert "Ana Pereira" in result


# -------------------------------------------------------------------------
# Cross-prompt invariants
# -------------------------------------------------------------------------


class TestPromptInvariants:
    """Cross-cutting invariants that all prompts must satisfy."""

    ALL_SYSTEM_PROMPTS = [
        ANAMNESIS_SYSTEM_PROMPT,
        PRESCRIPTION_SYSTEM_PROMPT,
        SUMMARY_SYSTEM_PROMPT,
        TRANSCRIPT_SYSTEM_PROMPT,
        INSIGHTS_SYSTEM_PROMPT,
    ]

    @pytest.mark.parametrize("prompt", ALL_SYSTEM_PROMPTS)
    def test_system_prompts_require_json_output(self, prompt: str) -> None:
        assert "JSON" in prompt

    @pytest.mark.parametrize("prompt", ALL_SYSTEM_PROMPTS)
    def test_system_prompts_are_in_pt_br(self, prompt: str) -> None:
        assert "Voce e" in prompt or "pt-BR" in prompt

    @pytest.mark.parametrize("prompt", ALL_SYSTEM_PROMPTS)
    def test_system_prompts_require_exclusive_json(self, prompt: str) -> None:
        assert "Sem texto antes" in prompt or "exclusivamente" in prompt

    @pytest.mark.parametrize("prompt", ALL_SYSTEM_PROMPTS)
    def test_system_prompts_have_validation_section(self, prompt: str) -> None:
        assert "VALIDACAO" in prompt

    @pytest.mark.parametrize("prompt", ALL_SYSTEM_PROMPTS)
    def test_system_prompts_minimum_length(self, prompt: str) -> None:
        assert len(prompt) > 500
