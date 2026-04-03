"""Port interface for authentication operations."""

from abc import ABC, abstractmethod

from deskai.domain.auth.value_objects import Tokens


class AuthProvider(ABC):
    """Abstract authentication provider."""

    @abstractmethod
    def authenticate(self, email: str, password: str) -> Tokens:
        """Authenticate with email and password. Returns tokens on success."""

    @abstractmethod
    def sign_out(self, access_token: str) -> None:
        """Invalidate all sessions for the given access token."""

    @abstractmethod
    def forgot_password(self, email: str) -> None:
        """Initiate the forgot-password flow for the given email."""

    @abstractmethod
    def confirm_forgot_password(
        self, email: str, confirmation_code: str, new_password: str
    ) -> None:
        """Complete the forgot-password flow with a confirmation code."""

    @abstractmethod
    def validate_ws_token(self, token: str) -> dict:
        """Validate a WebSocket JWT token and return identity claims.

        Returns a dict with at least ``doctor_id``, ``clinic_id``, and ``sub``.
        Raises ``AuthenticationError`` on any validation failure.
        """
