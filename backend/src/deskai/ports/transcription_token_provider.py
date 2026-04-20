"""Port interface for transcription token issuance."""

from abc import ABC, abstractmethod
from typing import Any


class TranscriptionTokenProvider(ABC):
    """Contract for issuing single-use transcription tokens."""

    @abstractmethod
    def create_single_use_token(self, scope: str = "realtime_scribe") -> dict[str, Any]:
        """Issue a single-use token for client-side realtime transcription.

        Returns a dict with at least: token, websocket_url, model_id,
        language_code, expires_at, expires_in_seconds.
        """
