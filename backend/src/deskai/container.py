"""Dependency wiring entrypoint for backend handlers."""

from dataclasses import dataclass

from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
from deskai.adapters.persistence.dynamodb_doctor_repository import (
    DynamoDBDoctorRepository,
)
from deskai.application.auth.authenticate import AuthenticateUseCase
from deskai.application.auth.check_entitlements import (
    CheckEntitlementsUseCase,
)
from deskai.application.auth.forgot_password import (
    ConfirmForgotPasswordUseCase,
    ForgotPasswordUseCase,
)
from deskai.application.auth.get_current_user import (
    GetCurrentUserUseCase,
)
from deskai.application.auth.sign_out import SignOutUseCase
from deskai.ports.auth_provider import AuthProvider
from deskai.ports.doctor_repository import DoctorRepository
from deskai.shared.config import Settings, load_settings


@dataclass(frozen=True)
class Container:
    """Resolved runtime dependencies for handler execution."""

    settings: Settings
    auth_provider: AuthProvider
    doctor_repo: DoctorRepository
    authenticate: AuthenticateUseCase
    sign_out: SignOutUseCase
    forgot_password: ForgotPasswordUseCase
    confirm_forgot_password: ConfirmForgotPasswordUseCase
    get_current_user: GetCurrentUserUseCase
    check_entitlements: CheckEntitlementsUseCase


def build_container() -> Container:
    """Create the dependency container with all auth wiring."""
    settings = load_settings()

    if not settings.cognito_user_pool_id or not settings.cognito_client_id:
        raise RuntimeError(
            "DESKAI_COGNITO_USER_POOL_ID and DESKAI_COGNITO_CLIENT_ID "
            "environment variables are required."
        )

    auth_provider = CognitoAuthProvider(
        user_pool_id=settings.cognito_user_pool_id,
        client_id=settings.cognito_client_id,
    )
    doctor_repo = DynamoDBDoctorRepository(
        table_name=settings.dynamodb_table,
    )

    return Container(
        settings=settings,
        auth_provider=auth_provider,
        doctor_repo=doctor_repo,
        authenticate=AuthenticateUseCase(
            auth_provider=auth_provider,
        ),
        sign_out=SignOutUseCase(
            auth_provider=auth_provider,
        ),
        forgot_password=ForgotPasswordUseCase(
            auth_provider=auth_provider,
        ),
        confirm_forgot_password=ConfirmForgotPasswordUseCase(
            auth_provider=auth_provider,
        ),
        get_current_user=GetCurrentUserUseCase(
            doctor_repo=doctor_repo,
        ),
        check_entitlements=CheckEntitlementsUseCase(
            doctor_repo=doctor_repo,
        ),
    )
