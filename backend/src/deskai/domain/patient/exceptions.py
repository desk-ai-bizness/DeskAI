"""Patient domain exceptions."""

from deskai.shared.errors import DeskAIError


class PatientNotFoundError(DeskAIError):
    """Raised when a patient cannot be found."""


class PatientValidationError(DeskAIError):
    """Raised when patient data fails validation."""
