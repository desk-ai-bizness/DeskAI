"""Unit tests for the authenticate use case."""

import unittest
from unittest.mock import MagicMock

from deskai.application.auth.authenticate import (
    AuthenticateUseCase,
)
from deskai.domain.auth.exceptions import AuthenticationError
from deskai.domain.auth.value_objects import Tokens


class AuthenticateUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_provider = MagicMock()
        self.use_case = AuthenticateUseCase(
            auth_provider=self.mock_provider,
        )

    def test_returns_tokens_on_success(self) -> None:
        expected = Tokens(
            access_token="a",
            refresh_token="r",
            expires_in=3600,
        )
        self.mock_provider.authenticate.return_value = expected
        result = self.use_case.execute(
            "user@test.com", "P@ssword123!"
        )
        self.assertEqual(result, expected)
        self.mock_provider.authenticate.assert_called_once_with(
            "user@test.com", "P@ssword123!"
        )

    def test_propagates_authentication_error(self) -> None:
        self.mock_provider.authenticate.side_effect = (
            AuthenticationError("bad")
        )
        with self.assertRaises(AuthenticationError):
            self.use_case.execute("user@test.com", "wrong")


if __name__ == "__main__":
    unittest.main()
