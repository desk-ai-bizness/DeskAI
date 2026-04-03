"""Shared error types for backend layers."""


class DeskAIError(Exception):
    """Base exception type for unexpected backend failures."""


class ConfigurationError(DeskAIError):
    """Raised when required runtime configuration is missing."""


class DomainValidationError(DeskAIError):
    """Raised when domain invariants are violated."""


class RepositoryError(DeskAIError):
    """Base exception for persistence-layer failures."""


class NotFoundError(RepositoryError):
    """Raised when a requested entity does not exist."""


class ConflictError(RepositoryError):
    """Raised on conditional-check failures (optimistic concurrency)."""


class ThrottleError(RepositoryError):
    """Raised after exhausting retries on DynamoDB throttle errors."""


class ConnectionError(RepositoryError):
    """Raised when DynamoDB is unreachable or times out."""
