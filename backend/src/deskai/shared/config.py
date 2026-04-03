"""Environment-driven application settings."""

from dataclasses import dataclass
from os import getenv


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


def load_settings() -> Settings:
    """Load backend settings from process environment."""

    return Settings(
        environment=getenv("DESKAI_ENV", "dev"),
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
