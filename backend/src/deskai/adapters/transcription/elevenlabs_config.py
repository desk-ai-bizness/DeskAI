"""ElevenLabs Scribe v2 provider configuration."""

import json
from dataclasses import dataclass

import boto3

from deskai.shared.logging import get_logger

logger = get_logger()

_DEFAULT_WS_ENDPOINT = "wss://api.elevenlabs.io/v1/speech-to-text/ws"
_DEFAULT_MODEL = "scribe_v2"
_DEFAULT_LANGUAGE = "pt"
_DEFAULT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class ElevenLabsConfig:
    """Immutable configuration for the ElevenLabs Scribe v2 provider."""

    api_key: str
    ws_endpoint: str = _DEFAULT_WS_ENDPOINT
    model: str = _DEFAULT_MODEL
    language: str = _DEFAULT_LANGUAGE
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS

    @property
    def http_endpoint(self) -> str:
        """Derive the HTTP endpoint from the WebSocket endpoint."""
        return (
            self.ws_endpoint.replace("wss://", "https://")
            .replace("ws://", "http://")
            .removesuffix("/ws")
        )


def load_elevenlabs_config(secret_name: str) -> ElevenLabsConfig:
    """Load ElevenLabs config from AWS Secrets Manager.

    The secret must contain a JSON object with key ``elevenlabs_api_key``.
    """
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])

    api_key = secret["elevenlabs_api_key"]

    logger.info(
        "elevenlabs_config_loaded",
        extra={"secret_name": secret_name},
    )

    return ElevenLabsConfig(api_key=api_key)
