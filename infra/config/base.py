"""Shared configuration types used by all CDK stacks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentConfig:
    """Immutable environment-specific infrastructure configuration."""

    environment: str
    aws_account_id: str
    aws_region: str
    deepgram_secret_name: str
    claude_secret_name: str

    @property
    def resource_prefix(self) -> str:
        return f"deskai-{self.environment}"
