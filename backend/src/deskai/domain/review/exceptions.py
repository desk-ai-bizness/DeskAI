"""Review domain exceptions."""

from deskai.shared.errors import DeskAIError


class ReviewNotAvailableError(DeskAIError):
    """Raised when review is requested for a consultation not ready for review."""

    def __init__(self, consultation_id: str, current_status: str) -> None:
        super().__init__(
            f"Review not available for consultation '{consultation_id}' "
            f"in status '{current_status}'"
        )
        self.consultation_id = consultation_id
        self.current_status = current_status


class ReviewNotEditableError(DeskAIError):
    """Raised when edits are attempted on a consultation not in review state."""

    def __init__(self, consultation_id: str, current_status: str) -> None:
        super().__init__(
            f"Cannot edit consultation '{consultation_id}' in status '{current_status}'"
        )
        self.consultation_id = consultation_id
        self.current_status = current_status


class FinalizationNotAllowedError(DeskAIError):
    """Raised when finalization is attempted on a consultation not ready."""

    def __init__(self, consultation_id: str, reason: str) -> None:
        super().__init__(f"Cannot finalize consultation '{consultation_id}': {reason}")
        self.consultation_id = consultation_id
        self.reason = reason


class ExportNotAllowedError(DeskAIError):
    """Raised when export is requested for a non-finalized consultation."""

    def __init__(self, consultation_id: str, current_status: str) -> None:
        super().__init__(
            f"Cannot export consultation '{consultation_id}' "
            f"in status '{current_status}'. Only finalized consultations can be exported."
        )
        self.consultation_id = consultation_id
        self.current_status = current_status


class ArtifactsIncompleteError(DeskAIError):
    """Raised when required artifacts are missing for review or finalization."""

    def __init__(self, consultation_id: str, missing: list[str]) -> None:
        missing_str = ", ".join(missing)
        super().__init__(
            f"Required artifacts missing for consultation '{consultation_id}': {missing_str}"
        )
        self.consultation_id = consultation_id
        self.missing = missing
