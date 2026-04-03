"""Shared configuration types used by all CDK stacks."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentConfig:
    """Immutable environment-specific infrastructure configuration."""

    environment: str
    aws_account_id: str
    aws_region: str
    deployed_app_origins: tuple[str, ...]
    deployed_website_origins: tuple[str, ...]
    elevenlabs_secret_name: str
    claude_secret_name: str
    monthly_budget_limit_usd: int = 5
    alert_email: str = ""
    acm_certificate_arn: str = ""
    website_domain_names: tuple[str, ...] = ()
    app_domain_names: tuple[str, ...] = ()

    @property
    def resource_prefix(self) -> str:
        return f"deskai-{self.environment}"

    @property
    def allowed_cors_origins(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys((*self.deployed_app_origins, *self.deployed_website_origins))
        )

    @property
    def cognito_callback_urls(self) -> tuple[str, ...]:
        return tuple(f"{origin}/auth/callback" for origin in self.deployed_app_origins)

    @property
    def cognito_logout_urls(self) -> tuple[str, ...]:
        return tuple(f"{origin}/logout" for origin in self.deployed_app_origins)

    @property
    def is_production(self) -> bool:
        return self.environment == "prod"

    @property
    def consultation_table_name(self) -> str:
        return f"{self.resource_prefix}-consultation-records"

    @property
    def artifacts_bucket_name(self) -> str:
        return f"{self.resource_prefix}-artifacts"

    @property
    def website_bucket_name(self) -> str:
        return f"{self.resource_prefix}-website"

    @property
    def app_bucket_name(self) -> str:
        return f"{self.resource_prefix}-app"

    @property
    def user_pool_name(self) -> str:
        return f"{self.resource_prefix}-user-pool"

    @property
    def http_api_name(self) -> str:
        return f"{self.resource_prefix}-http-api"

    @property
    def websocket_api_name(self) -> str:
        return f"{self.resource_prefix}-ws-api"

    @property
    def cognito_secret_name(self) -> str:
        """Derive the Cognito client secret name from the environment."""
        return f"deskai/{self.environment}/cognito"
