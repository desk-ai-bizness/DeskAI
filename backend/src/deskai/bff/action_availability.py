"""Action availability rules based on consultation status."""

from deskai.domain.consultation.entities import ConsultationStatus

_STATUS_ACTIONS: dict[ConsultationStatus, set[str]] = {
    ConsultationStatus.STARTED: {"can_start_recording"},
    ConsultationStatus.RECORDING: {"can_stop_recording"},
    ConsultationStatus.IN_PROCESSING: set(),
    ConsultationStatus.PROCESSING_FAILED: {"can_retry_processing"},
    ConsultationStatus.DRAFT_GENERATED: {"can_open_review"},
    ConsultationStatus.UNDER_PHYSICIAN_REVIEW: {
        "can_edit_review",
        "can_finalize",
    },
    ConsultationStatus.FINALIZED: {"can_export"},
}

_ALL_ACTION_KEYS = (
    "can_start_recording",
    "can_stop_recording",
    "can_retry_processing",
    "can_open_review",
    "can_edit_review",
    "can_finalize",
    "can_export",
)


def compute_actions(
    status: ConsultationStatus,
    export_enabled: bool = True,
) -> dict[str, bool]:
    """Determine available actions based on consultation status."""
    enabled = _STATUS_ACTIONS.get(status, set())
    actions = {key: key in enabled for key in _ALL_ACTION_KEYS}
    if not export_enabled:
        actions["can_export"] = False
    return actions


def compute_warnings(
    status: ConsultationStatus,
    error_details: dict | None = None,
) -> list[dict[str, str]]:
    """Generate warnings based on consultation state."""
    warnings: list[dict[str, str]] = []
    if status == ConsultationStatus.PROCESSING_FAILED:
        message = "Processing failed."
        if error_details and "reason" in error_details:
            message = f"Processing failed: {error_details['reason']}."
        warnings.append({"type": "processing_failed", "message": message})
    return warnings
