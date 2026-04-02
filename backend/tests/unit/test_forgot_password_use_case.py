"""Unit tests for the forgot-password use cases."""

import unittest
from unittest.mock import MagicMock

from deskai.application.auth.forgot_password import (
    ConfirmForgotPasswordUseCase,
    ForgotPasswordUseCase,
)
from deskai.domain.auth.exceptions import AuthenticationError


class ForgotPasswordUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_provider = MagicMock()
        self.use_case = ForgotPasswordUseCase(
            auth_provider=self.mock_provider,
        )

    def test_forgot_password_success(self) -> None:
        self.use_case.execute("user@test.com")
        self.mock_provider.forgot_password.assert_called_once_with(
            "user@test.com"
        )

    def test_forgot_password_propagates_error(self) -> None:
        self.mock_provider.forgot_password.side_effect = (
            AuthenticationError("Password reset failed.")
        )
        with self.assertRaises(AuthenticationError):
            self.use_case.execute("user@test.com")


class ConfirmForgotPasswordUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_provider = MagicMock()
        self.use_case = ConfirmForgotPasswordUseCase(
            auth_provider=self.mock_provider,
        )

    def test_confirm_forgot_password_success(self) -> None:
        self.use_case.execute(
            "user@test.com", "123456", "NewP@ss1!"
        )
        self.mock_provider.confirm_forgot_password.assert_called_once_with(
            "user@test.com", "123456", "NewP@ss1!"
        )

    def test_confirm_forgot_password_invalid_code(self) -> None:
        self.mock_provider.confirm_forgot_password.side_effect = (
            AuthenticationError("Invalid or expired confirmation code.")
        )
        with self.assertRaises(AuthenticationError):
            self.use_case.execute(
                "user@test.com", "wrong-code", "NewP@ss1!"
            )


if __name__ == "__main__":
    unittest.main()
