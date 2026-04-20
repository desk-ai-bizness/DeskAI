"""ElevenLabs single-use token adapter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from deskai.adapters.transcription.elevenlabs_config import ElevenLabsConfig
from deskai.domain.transcription.exceptions import (
    ProviderUnavailableError,
)
from deskai.ports.transcription_token_provider import TranscriptionTokenProvider
from deskai.shared.logging import get_logger

logger = get_logger()

_TOKEN_TTL_SECONDS = 900  # 15 minutes
_REALTIME_WS_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
_MODEL_ID = "scribe_v2_realtime"
_LANGUAGE_CODE = "pt"


class ElevenLabsTokenProvider(TranscriptionTokenProvider):
    """Issue single-use ElevenLabs tokens for client-side realtime scribe."""

    def __init__(self, config: ElevenLabsConfig) -> None:
        self._config = config

    def create_single_use_token(self, scope: str = "realtime_scribe") -> dict[str, Any]:
        """Call ElevenLabs token API and return metadata for frontend use."""
        try:
            response = httpx.post(
                f"{self._config.http_endpoint}/tokens",
                headers={"xi-api-key": self._config.api_key},
                json={"scope": scope, "ttl_seconds": _TOKEN_TTL_SECONDS},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "elevenlabs_token_request_failed",
                extra={"status": exc.response.status_code},
            )
            raise ProviderUnavailableError(
                f"ElevenLabs token API error ({exc.response.status_code})"
            ) from exc
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.error("elevenlabs_token_request_error")
            raise ProviderUnavailableError(
                f"Cannot reach ElevenLabs token API: {exc}"
            ) from exc

        now = datetime.now(tz=UTC)
        expires_at = now + timedelta(seconds=_TOKEN_TTL_SECONDS)

        token = data.get("token", "")

        logger.info("elevenlabs_token_issued")

        return {
            "token": token,
            "websocket_url": _REALTIME_WS_URL,
            "model_id": _MODEL_ID,
            "language_code": _LANGUAGE_CODE,
            "expires_at": expires_at.isoformat(),
            "expires_in_seconds": _TOKEN_TTL_SECONDS,
        }
