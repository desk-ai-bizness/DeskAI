"""Transcription domain exceptions."""

from deskai.shared.errors import DeskAIError


class TranscriptionError(DeskAIError):
    """Base exception for all transcription-related failures."""


class ProviderSessionError(TranscriptionError):
    """Raised when the transcription provider session encounters an error."""


class TranscriptionIncompleteError(TranscriptionError):
    """Raised when a transcription cannot be completed."""


class NormalizationError(TranscriptionError):
    """Raised when raw provider output cannot be normalized."""


class ProviderUnavailableError(TranscriptionError):
    """Raised when the transcription provider is unreachable."""
