"""Consultation domain exceptions."""

from deskai.shared.errors import DeskAIError


class InvalidStatusTransitionError(DeskAIError):
    """Raised when a consultation status transition is not allowed."""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(
            f"Invalid status transition from '{from_status}' to '{to_status}'"
        )
        self.from_status = from_status
        self.to_status = to_status


class ConsultationNotFoundError(DeskAIError):
    """Raised when a consultation cannot be found."""


class ConsultationOwnershipError(DeskAIError):
    """Raised when a user tries to access a consultation they do not own."""


class ConsultationAlreadyFinalizedError(DeskAIError):
    """Raised when an operation is attempted on a finalized consultation."""
