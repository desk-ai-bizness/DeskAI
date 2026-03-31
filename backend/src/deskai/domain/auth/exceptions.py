"""Auth domain exceptions."""

from deskai.shared.errors import DeskAIError


class AuthenticationError(DeskAIError):
    """Invalid credentials or authentication failure."""


class AccountNotVerifiedError(DeskAIError):
    """Account exists but email has not been verified."""


class AccountDisabledError(DeskAIError):
    """Account has been disabled by an administrator."""


class DoctorProfileNotFoundError(DeskAIError):
    """Cognito user exists but no matching doctor profile was found."""


class UnauthorizedAccessError(DeskAIError):
    """Authenticated user does not have permission for this resource."""


class PlanLimitExceededError(DeskAIError):
    """Monthly consultation limit for the current plan has been reached."""


class TrialExpiredError(DeskAIError):
    """Free trial period has expired."""
