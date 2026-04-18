"""BFF UI config labels -- pt-BR user-facing strings."""

from deskai.domain.consultation.entities import ConsultationStatus


def get_labels() -> dict[str, str]:
    """Return the 10 required UI label strings in pt-BR."""
    return {
        "consultation_list_title": "Consultas",
        "new_consultation_button": "Nova Consulta",
        "start_recording_button": "Iniciar Gravação",
        "stop_recording_button": "Parar Gravação",
        "review_title": "Revisão da Consulta",
        "finalize_button": "Finalizar",
        "export_button": "Exportar",
        "ai_disclaimer": (
            "Conteúdo gerado por IA"
            " — sujeito a revisão médica."
        ),
        "completeness_warning": (
            "Alguns campos podem estar incompletos."
            " Revise antes de finalizar."
        ),
        "live_session_header": "Sessão ao Vivo",
    }


def get_status_labels() -> dict[str, str]:
    """Return pt-BR display labels for every ConsultationStatus value."""
    return {
        ConsultationStatus.STARTED.value: "Iniciada",
        ConsultationStatus.RECORDING.value: "Gravando",
        ConsultationStatus.IN_PROCESSING.value: "Em Processamento",
        ConsultationStatus.PROCESSING_FAILED.value: "Falha no Processamento",
        ConsultationStatus.DRAFT_GENERATED.value: "Rascunho Gerado",
        ConsultationStatus.UNDER_PHYSICIAN_REVIEW.value: "Em Revisão Médica",
        ConsultationStatus.FINALIZED.value: "Finalizada",
    }


def get_insight_categories() -> dict[str, dict[str, str]]:
    """Return the 3 insight category configs with label, icon, and severity."""
    return {
        "documentation_gap": {
            "label": "Lacuna de Documentação",
            "icon": "info",
            "severity": "low",
        },
        "consistency_issue": {
            "label": "Problema de Consistência",
            "icon": "warning",
            "severity": "medium",
        },
        "clinical_attention": {
            "label": "Atenção Clínica",
            "icon": "alert",
            "severity": "high",
        },
    }
