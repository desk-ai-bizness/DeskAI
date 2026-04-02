"""BFF UI config assembler -- composes the full UIConfigView payload."""

from deskai.bff.feature_flags.evaluator import evaluate_flags
from deskai.bff.ui_config.labels import (
    get_insight_categories,
    get_labels,
    get_status_labels,
)
from deskai.bff.ui_config.screen_config import (
    get_review_screen_config,
)
from deskai.domain.auth.value_objects import PlanType


def assemble_ui_config(plan_type: PlanType) -> dict:
    """Build the complete UI config response for the given plan type."""
    flags = evaluate_flags(plan_type)
    return {
        "version": "1.0",
        "locale": "pt-BR",
        "labels": get_labels(),
        "review_screen": get_review_screen_config(),
        "insight_categories": get_insight_categories(),
        "status_labels": get_status_labels(),
        "feature_flags": {
            "export_enabled": bool(
                flags.get("export_pdf_enabled", False)
            ),
            "insights_enabled": bool(
                flags.get("insights_enabled", False)
            ),
            "audio_playback_enabled": bool(
                flags.get("audio_playback_enabled", False)
            ),
        },
    }
