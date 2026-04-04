"""AI pipeline domain services."""

from deskai.domain.ai_pipeline.value_objects import InsightCategory, InsightSeverity

_VALID_CATEGORIES = {c.value for c in InsightCategory}
_VALID_SEVERITIES = {s.value for s in InsightSeverity}


class ArtifactValidator:
    """Validates structured LLM outputs against expected schemas."""

    ANAMNESIS_REQUIRED_FIELDS = [
        "queixa_principal",
        "historia_doenca_atual",
        "historico_medico_pregresso",
        "medicamentos_em_uso",
        "alergias",
        "revisao_de_sistemas",
        "achados_exame_fisico",
        "observacoes_adicionais",
        "campos_incompletos",
    ]

    SUMMARY_REQUIRED_FIELDS = [
        "subjetivo",
        "objetivo",
        "avaliacao",
        "plano",
        "codigos_cid10_sugeridos",
        "aviso_revisao",
    ]

    INSIGHTS_REQUIRED_FIELDS = [
        "observacoes",
        "resumo_observacoes",
        "aviso_revisao",
    ]

    @staticmethod
    def validate_anamnesis(data: dict) -> list[str]:
        """Return list of missing required fields for an anamnesis artifact."""
        return [f for f in ArtifactValidator.ANAMNESIS_REQUIRED_FIELDS if f not in data]

    @staticmethod
    def validate_summary(data: dict) -> list[str]:
        """Return list of missing required fields for a summary artifact."""
        return [f for f in ArtifactValidator.SUMMARY_REQUIRED_FIELDS if f not in data]

    @staticmethod
    def validate_insights(data: dict) -> list[str]:
        """Return missing fields and validation errors for an insights artifact."""
        missing = [f for f in ArtifactValidator.INSIGHTS_REQUIRED_FIELDS if f not in data]
        missing.extend(ArtifactValidator.validate_insight_categories(data))
        missing.extend(ArtifactValidator.validate_insight_evidence(data))
        return missing

    @staticmethod
    def validate_insight_categories(insights_data: dict) -> list[str]:
        """Check each insight has a valid InsightCategory value."""
        errors: list[str] = []
        for i, obs in enumerate(insights_data.get("observacoes", [])):
            cat = obs.get("categoria", "")
            if cat not in _VALID_CATEGORIES:
                errors.append(f"observacoes[{i}].categoria: invalid value '{cat}'")
        return errors

    @staticmethod
    def validate_insight_evidence(insights_data: dict) -> list[str]:
        """Check each insight has evidencia with trecho and contexto."""
        errors: list[str] = []
        for i, obs in enumerate(insights_data.get("observacoes", [])):
            ev = obs.get("evidencia")
            if ev is None:
                errors.append(f"observacoes[{i}].evidencia: missing")
                continue
            if "trecho" not in ev:
                errors.append(f"observacoes[{i}].evidencia.trecho: missing")
            if "contexto" not in ev:
                errors.append(f"observacoes[{i}].evidencia.contexto: missing")
        return errors


class EvidenceLinker:
    """Links insight evidence to transcript content."""

    @staticmethod
    def verify_evidence_in_transcript(transcript_text: str, insights_data: dict) -> list[dict]:
        """Check each insight's trecho is a substring of transcript (case-insensitive).

        Returns list of unverified insights with their trecho and index.
        """
        unverified: list[dict] = []
        transcript_lower = transcript_text.lower()
        for i, obs in enumerate(insights_data.get("observacoes", [])):
            ev = obs.get("evidencia")
            if ev is None:
                unverified.append({"index": i, "trecho": None, "reason": "no evidence"})
                continue
            trecho = ev.get("trecho", "")
            if trecho.lower() not in transcript_lower:
                unverified.append({"index": i, "trecho": trecho, "reason": "not found"})
        return unverified

    @staticmethod
    def count_by_category(insights_data: dict) -> dict[str, int]:
        """Count insights grouped by category."""
        counts: dict[str, int] = {}
        for obs in insights_data.get("observacoes", []):
            cat = obs.get("categoria", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    @staticmethod
    def count_by_severity(insights_data: dict) -> dict[str, int]:
        """Count insights grouped by severity."""
        counts: dict[str, int] = {}
        for obs in insights_data.get("observacoes", []):
            sev = obs.get("severidade", "unknown")
            counts[sev] = counts.get(sev, 0) + 1
        return counts
