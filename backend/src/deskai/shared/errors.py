"""Shared error types for backend layers."""


class DeskAIError(Exception):
    """Base exception type for unexpected backend failures."""


class ConfigurationError(DeskAIError):
    """Raised when required runtime configuration is missing."""


class DomainValidationError(DeskAIError):
    """Raised when domain invariants are violated."""
