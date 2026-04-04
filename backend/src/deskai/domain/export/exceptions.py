"""Export domain exceptions."""

from deskai.shared.errors import DeskAIError


class ExportGenerationError(DeskAIError):
    """Raised when PDF generation fails."""

    def __init__(self, consultation_id: str, reason: str) -> None:
        super().__init__(f"Export generation failed for consultation '{consultation_id}': {reason}")
        self.consultation_id = consultation_id
        self.reason = reason
