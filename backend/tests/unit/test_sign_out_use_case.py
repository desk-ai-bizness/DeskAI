"""Unit tests for the sign-out use case."""

import unittest
from unittest.mock import MagicMock

from deskai.application.auth.sign_out import SignOutUseCase
from deskai.domain.auth.exceptions import AuthenticationError


class SignOutUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_provider = MagicMock()
        self.use_case = SignOutUseCase(
            auth_provider=self.mock_provider,
        )

    def test_sign_out_success(self) -> None:
        self.use_case.execute("valid-access-token")
        self.mock_provider.sign_out.assert_called_once_with(
            "valid-access-token"
        )

    def test_sign_out_invalid_token(self) -> None:
        self.mock_provider.sign_out.side_effect = (
            AuthenticationError("Invalid or expired token.")
        )
        with self.assertRaises(AuthenticationError):
            self.use_case.execute("expired-token")


if __name__ == "__main__":
    unittest.main()
