"""AWS production environment infrastructure configuration."""

from config.base import EnvironmentConfig

PROD_CONFIG = EnvironmentConfig(
    environment="prod",
    aws_account_id="183992492124",
    aws_region="sa-east-1",
    deployed_app_origins=("https://app.deskai.com.br",),
    deployed_website_origins=(
        "https://deskai.com.br",
        "https://www.deskai.com.br",
    ),
    elevenlabs_secret_name="deskai/prod/elevenlabs",
    claude_secret_name="deskai/prod/claude",
)
