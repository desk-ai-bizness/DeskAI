"""Environment-driven application settings."""

from dataclasses import dataclass
from os import getenv

from deskai.shared.errors import ConfigurationError


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    environment: str
    contract_version: str
    dynamodb_table: str
    artifacts_bucket: str
    ui_config_key: str
    elevenlabs_secret_name: str
    claude_secret_name: str
    cognito_secret_name: str
    cognito_user_pool_id: str
    cognito_client_id: str
    websocket_url: str
    max_session_duration_minutes: int


DEFAULT_DYNAMODB_TABLE = "deskai-dev-consultation-records"
DEFAULT_ARTIFACTS_BUCKET = "deskai-dev-artifacts"
DEFAULT_UI_CONFIG_KEY = "CONFIG#ui"

_PROD_REQUIRED_VARS = (
    "DESKAI_DYNAMODB_TABLE",
    "DESKAI_ARTIFACTS_BUCKET",
    "DESKAI_ELEVENLABS_SECRET_NAME",
    "DESKAI_CLAUDE_SECRET_NAME",
    "DESKAI_COGNITO_CLIENT_SECRET_NAME",
    "DESKAI_COGNITO_USER_POOL_ID",
    "DESKAI_COGNITO_CLIENT_ID",
    "DESKAI_WEBSOCKET_URL",
)


def _is_strict_environment(env: str) -> bool:
    """Return True if the environment enforces required env vars."""
    return env in ("prod", "staging")


def load_settings() -> Settings:
    """Load backend settings from process environment."""

    env = getenv("DESKAI_ENV", "dev")

    if _is_strict_environment(env):
        missing = [v for v in _PROD_REQUIRED_VARS if not getenv(v)]
        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    return Settings(
        environment=env,
        contract_version=getenv("DESKAI_CONTRACT_VERSION", "v1"),
        dynamodb_table=getenv("DESKAI_DYNAMODB_TABLE", DEFAULT_DYNAMODB_TABLE),
        artifacts_bucket=getenv("DESKAI_ARTIFACTS_BUCKET", DEFAULT_ARTIFACTS_BUCKET),
        ui_config_key=getenv("DESKAI_UI_CONFIG_KEY", DEFAULT_UI_CONFIG_KEY),
        elevenlabs_secret_name=getenv("DESKAI_ELEVENLABS_SECRET_NAME", "deskai/dev/elevenlabs"),
        claude_secret_name=getenv("DESKAI_CLAUDE_SECRET_NAME", "deskai/dev/claude"),
        cognito_secret_name=getenv(
            "DESKAI_COGNITO_CLIENT_SECRET_NAME",
            "deskai/dev/cognito",
        ),
        cognito_user_pool_id=getenv("DESKAI_COGNITO_USER_POOL_ID", ""),
        cognito_client_id=getenv("DESKAI_COGNITO_CLIENT_ID", ""),
        websocket_url=getenv("DESKAI_WEBSOCKET_URL", "wss://localhost:3001"),
        max_session_duration_minutes=int(
            getenv("DESKAI_MAX_SESSION_DURATION_MINUTES", "60")
        ),
    )
