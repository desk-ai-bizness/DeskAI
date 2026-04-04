"""BFF view builders for review, finalize, and export responses."""

from typing import Any

from deskai.domain.consultation.entities import Consultation
from deskai.domain.export.entities import ExportArtifact
from deskai.domain.review.entities import ReviewPayload


def build_review_view(
    payload: ReviewPayload,
    ui_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the ReviewView contract per 03-contract-inventory.md."""
    insights_view = []
    for i, insight in enumerate(payload.insights or []):
        evidence_list = []
        evidence = insight.get("evidencia")
        if evidence:
            evidence_list.append(
                {
                    "text": evidence.get("trecho", ""),
                    "context": evidence.get("contexto", ""),
                }
            )
        insights_view.append(
            {
                "insight_id": str(i),
                "category": insight.get("categoria", ""),
                "description": insight.get("descricao", ""),
                "severity": insight.get("severidade", ""),
                "evidence": evidence_list,
                "status": "pending",
                "physician_note": None,
            }
        )

    view: dict[str, Any] = {
        "consultation_id": payload.consultation_id,
        "status": "under_physician_review",
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
