"""Sign out the current user."""

from dataclasses import dataclass

from deskai.ports.auth_provider import AuthProvider


@dataclass(frozen=True)
class SignOutUseCase:
    """Invalidate all sessions for the authenticated user."""

    auth_provider: AuthProvider

    def execute(self, access_token: str) -> None:
        self.auth_provider.sign_out(access_token)
