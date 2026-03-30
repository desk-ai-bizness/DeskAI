"""Development environment infrastructure configuration."""

from config.base import EnvironmentConfig

DEV_CONFIG = EnvironmentConfig(
    environment="dev",
    aws_account_id="111111111111",
    aws_region="us-east-1",
    deepgram_secret_name="deskai/dev/deepgram",
    claude_secret_name="deskai/dev/claude",
)
