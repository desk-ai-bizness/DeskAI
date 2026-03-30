"""Authentication stack for Cognito user management."""

from aws_cdk import Duration, Stack
from aws_cdk import aws_cognito as cognito

from config.base import EnvironmentConfig
from constructs import Construct


class AuthStack(Stack):
    """Provision Cognito resources for email and password authentication."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: EnvironmentConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config

        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=config.user_pool_name,
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            mfa=cognito.Mfa.OFF,
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False)
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7),
            ),
        )

        self.user_pool_client = self.user_pool.add_client(
            "UserPoolClient",
            user_pool_client_name=f"{config.resource_prefix}-web-client",
            generate_secret=False,
            prevent_user_existence_errors=True,
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=list(config.cognito_callback_urls),
                logout_urls=list(config.cognito_logout_urls),
            ),
        )

        self.user_pool_domain = self.user_pool.add_domain(
            "HostedDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=f"{config.resource_prefix}-auth"
            ),
        )
