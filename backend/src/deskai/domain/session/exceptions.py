"""Session domain exceptions."""

from deskai.shared.errors import DeskAIError


class SessionNotFoundError(DeskAIError):
    """Raised when a session cannot be found."""


class SessionAlreadyActiveError(DeskAIError):
    """Raised when a session is already active for a consultation."""


class SessionNotActiveError(DeskAIError):
    """Raised when an operation requires an active session but none exists."""


class InvalidSessionStateError(DeskAIError):
    """Raised when a session is in an invalid state for the requested operation."""


class AudioChunkRejectedError(DeskAIError):
    """Raised when an audio chunk cannot be accepted."""


class GracePeriodExpiredError(DeskAIError):
    """Raised when the reconnection grace period has expired."""


class SessionOwnershipError(DeskAIError):
    """Raised when a doctor tries to operate on a session they do not own."""
