"""BFF view builders for review, finalize, and export responses."""

from typing import Any

from deskai.domain.consultation.entities import Consultation
from deskai.domain.export.entities import ExportArtifact
from deskai.domain.review.entities import InsightAction
from deskai.domain.review.entities import ReviewPayload


_CATEGORY_MAP = {
    "lacuna_de_documentacao": "documentation_gap",
    "inconsistencia": "consistency_issue",
    "atencao_clinica": "clinical_attention",
}


def build_review_view(
    payload: ReviewPayload,
    ui_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the ReviewView contract per 03-contract-inventory.md."""
    actions_by_id = {
        item["insight_id"]: item for item in (payload.insight_actions or []) if item.get("insight_id")
    }
    insights_view = []
    for i, insight in enumerate(payload.insights or []):
        insight_id = str(i)
        evidence_list = []
        evidence = insight.get("evidencia")
        if evidence:
            evidence_list.append(
                {
                    "text": evidence.get("trecho", ""),
                    "context": evidence.get("contexto", ""),
                }
            )
        action_data = actions_by_id.get(insight_id, {})
        insights_view.append(
            {
                "insight_id": insight_id,
                "category": _CATEGORY_MAP.get(
                    insight.get("categoria", ""),
                    insight.get("categoria", ""),
                ),
                "description": insight.get("descricao", ""),
                "severity": insight.get("severidade", ""),
                "evidence": evidence_list,
                "status": action_data.get("action", InsightAction.PENDING.value),
                "physician_note": action_data.get("physician_note"),
            }
        )

    view: dict[str, Any] = {
        "consultation_id": payload.consultation_id,
        "status": payload.status.value,
        "medical_history": {
            "content": payload.medical_history or {},
            "edited_by_physician": payload.medical_history_edited,
            "completeness_warning": payload.completeness_warning,
        },
        "summary": {
            "content": payload.summary or {},
            "edited_by_physician": payload.summary_edited,
            "completeness_warning": payload.completeness_warning,
        },
        "insights": insights_view,
    }

    if payload.transcript_segments is not None:
        view["transcript"] = {
            "segments": payload.transcript_segments,
        }

    if ui_config:
        view["ui_config"] = ui_config

    return view


def build_finalize_view(consultation: Consultation) -> dict[str, Any]:
    """Assemble the FinalizeView contract."""
    return {
        "consultation_id": consultation.consultation_id,
        "status": consultation.status.value,
        "finalized_at": consultation.finalized_at,
        "finalized_by": consultation.finalized_by,
    }


def build_export_view(artifact: ExportArtifact) -> dict[str, Any]:
    """Assemble the ExportView contract."""
    return {
        "consultation_id": artifact.consultation_id,
        "export_url": artifact.presigned_url,
        "expires_at": artifact.expires_at,
        "format": artifact.format.value,
    }
