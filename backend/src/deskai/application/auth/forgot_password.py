"""Password reset use cases."""

from dataclasses import dataclass

from deskai.ports.auth_provider import AuthProvider


@dataclass(frozen=True)
class ForgotPasswordUseCase:
    """Initiate the forgot-password flow."""

    auth_provider: AuthProvider

    def execute(self, email: str) -> None:
        self.auth_provider.forgot_password(email)


@dataclass(frozen=True)
class ConfirmForgotPasswordUseCase:
    """Complete the forgot-password flow with a confirmation code."""

    auth_provider: AuthProvider

    def execute(
        self,
        email: str,
        confirmation_code: str,
        new_password: str,
    ) -> None:
        self.auth_provider.confirm_forgot_password(
            email, confirmation_code, new_password
        )
