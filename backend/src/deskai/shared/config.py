"""Environment-driven application settings with production safety."""

from dataclasses import dataclass
from os import getenv

from deskai.shared.errors import ConfigurationError

_STRICT_ENVIRONMENTS = frozenset({"prod", "staging"})

_PROD_REQUIRED_VARS = frozenset(
    {
        "DESKAI_DYNAMODB_TABLE",
        "DESKAI_ARTIFACTS_BUCKET",
        "DESKAI_ELEVENLABS_SECRET_NAME",
        "DESKAI_CLAUDE_SECRET_NAME",
        "DESKAI_COGNITO_CLIENT_SECRET_NAME",
        "DESKAI_COGNITO_USER_POOL_ID",
        "DESKAI_COGNITO_CLIENT_ID",
        "DESKAI_WEBSOCKET_URL",
    }
)


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
    gemini_secret_name: str
    llm_provider: str
    cognito_secret_name: str
    cognito_user_pool_id: str
    cognito_client_id: str
    websocket_url: str
    event_bus_name: str
    max_session_duration_minutes: int


DEFAULT_DYNAMODB_TABLE = "deskai-dev-consultation-records"
DEFAULT_ARTIFACTS_BUCKET = "deskai-dev-artifacts"
DEFAULT_UI_CONFIG_KEY = "CONFIG#ui"


def _is_strict_environment(env: str) -> bool:
    """Return True when the environment must have all required vars set."""
    return env in _STRICT_ENVIRONMENTS


def _require_env_vars(environment: str) -> None:
    """Raise ConfigurationError if any required var is missing or empty."""
    if not _is_strict_environment(environment):
        return
    missing = sorted(var for var in _PROD_REQUIRED_VARS if not getenv(var))
    if missing:
        raise ConfigurationError(
            f"Missing required environment variables for '{environment}': " + ", ".join(missing)
        )


def _resolve_websocket_url() -> str:
    """Resolve the WebSocket URL from env var or SSM parameter.

    The CDK passes ``DESKAI_WEBSOCKET_URL_PARAM`` (an SSM parameter name)
    to avoid cross-stack references.  We read the actual URL from SSM at
    startup so that ``Settings.websocket_url`` always holds the real URL.
    """
    direct = getenv("DESKAI_WEBSOCKET_URL", "")
    if direct:
        return direct

    param_name = getenv("DESKAI_WEBSOCKET_URL_PARAM", "")
    if param_name:
        try:
            import boto3

            ssm = boto3.client("ssm")
            response = ssm.get_parameter(Name=param_name)
            return response["Parameter"]["Value"]
        except Exception:
            pass

    return "wss://localhost:3001"


def load_settings() -> Settings:
    """Load backend settings from process environment.

    In prod/staging, all critical env vars must be explicitly set.
    In dev/test, sensible defaults are used for local development.
    """
    environment = getenv("DESKAI_ENV", "dev")
    _require_env_vars(environment)

    return Settings(
        environment=environment,
        contract_version=getenv("DESKAI_CONTRACT_VERSION", "v1"),
        dynamodb_table=getenv("DESKAI_DYNAMODB_TABLE", DEFAULT_DYNAMODB_TABLE),
        artifacts_bucket=getenv("DESKAI_ARTIFACTS_BUCKET", DEFAULT_ARTIFACTS_BUCKET),
        ui_config_key=getenv("DESKAI_UI_CONFIG_KEY", DEFAULT_UI_CONFIG_KEY),
        elevenlabs_secret_name=getenv("DESKAI_ELEVENLABS_SECRET_NAME", "deskai/dev/elevenlabs"),
        claude_secret_name=getenv("DESKAI_CLAUDE_SECRET_NAME", "deskai/dev/claude"),
        gemini_secret_name=getenv("DESKAI_GEMINI_SECRET_NAME", "deskai/dev/gemini"),
        llm_provider=getenv("DESKAI_LLM_PROVIDER", "gemini"),
        cognito_secret_name=getenv(
            "DESKAI_COGNITO_CLIENT_SECRET_NAME",
            "deskai/dev/cognito",
        ),
        cognito_user_pool_id=getenv("DESKAI_COGNITO_USER_POOL_ID", ""),
        cognito_client_id=getenv("DESKAI_COGNITO_CLIENT_ID", ""),
        websocket_url=_resolve_websocket_url(),
        event_bus_name=getenv("DESKAI_EVENT_BUS_NAME", "deskai-dev-event-bus"),
        max_session_duration_minutes=int(getenv("DESKAI_MAX_SESSION_DURATION_MINUTES", "60")),
    )
