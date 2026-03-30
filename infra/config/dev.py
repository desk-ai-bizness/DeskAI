"""AWS development environment infrastructure configuration."""

from config.base import EnvironmentConfig

DEV_CONFIG = EnvironmentConfig(
    environment="dev",
    aws_account_id="183992492124",
    aws_region="us-east-1",
    deployed_app_origins=("https://app.dev.deskai.com.br",),
    deployed_website_origins=("https://dev.deskai.com.br",),
    deepgram_secret_name="deskai/dev/deepgram",
    claude_secret_name="deskai/dev/claude",
)
