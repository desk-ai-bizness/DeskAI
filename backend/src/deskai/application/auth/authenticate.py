"""Authenticate a user with email and password."""

from dataclasses import dataclass

from deskai.domain.auth.value_objects import Tokens
from deskai.ports.auth_provider import AuthProvider


@dataclass(frozen=True)
class AuthenticateUseCase:
    """Verify credentials and return session tokens."""

    auth_provider: AuthProvider

    def execute(self, email: str, password: str) -> Tokens:
        return self.auth_provider.authenticate(email, password)
