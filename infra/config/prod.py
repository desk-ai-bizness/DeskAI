"""Production environment infrastructure configuration."""

from config.base import EnvironmentConfig

PROD_CONFIG = EnvironmentConfig(
    environment="prod",
    aws_account_id="222222222222",
    aws_region="us-east-1",
    deepgram_secret_name="deskai/prod/deepgram",
    claude_secret_name="deskai/prod/claude",
)
