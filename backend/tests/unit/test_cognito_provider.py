"""Unit tests for the Cognito authentication provider adapter."""

import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
from deskai.domain.auth.exceptions import (
    AccountNotVerifiedError,
    AuthenticationError,
)
from deskai.domain.auth.value_objects import Tokens


def _client_error(code: str) -> ClientError:
    """Build a botocore ClientError with the given error code."""
    return ClientError(
        {"Error": {"Code": code, "Message": "test"}},
        "TestOperation",
    )


@patch("deskai.adapters.auth.cognito_provider.boto3")
class CognitoAuthProviderTest(unittest.TestCase):
    def _make_provider(self, mock_boto3: MagicMock) -> CognitoAuthProvider:
        self.mock_client = MagicMock()
        mock_boto3.client.return_value = self.mock_client
        return CognitoAuthProvider(
            user_pool_id="pool-123",
            client_id="client-abc",
        )

    # --- authenticate ---

    def test_authenticate_success(self, mock_boto3: MagicMock) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "access-tok",
                "RefreshToken": "refresh-tok",
                "ExpiresIn": 7200,
            }
        }

        result = provider.authenticate("doc@clinic.com", "s3cret")

        self.assertEqual(
            result,
            Tokens(
                access_token="access-tok",
                refresh_token="refresh-tok",
                expires_in=7200,
            ),
        )
        self.mock_client.initiate_auth.assert_called_once_with(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": "doc@clinic.com",
                "PASSWORD": "s3cret",
            },
            ClientId="client-abc",
        )

    def test_authenticate_not_authorized(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.initiate_auth.side_effect = _client_error(
            "NotAuthorizedException"
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.authenticate("doc@clinic.com", "wrong")
        self.assertIn("Invalid email or password", str(ctx.exception))

    def test_authenticate_user_not_confirmed(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.initiate_auth.side_effect = _client_error(
            "UserNotConfirmedException"
        )

        with self.assertRaises(AccountNotVerifiedError):
            provider.authenticate("doc@clinic.com", "pass")

    def test_authenticate_user_not_found(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.initiate_auth.side_effect = _client_error(
            "UserNotFoundException"
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.authenticate("ghost@clinic.com", "pass")
        self.assertIn("Invalid email or password", str(ctx.exception))

    def test_authenticate_unknown_error(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.initiate_auth.side_effect = _client_error(
            "InternalErrorException"
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.authenticate("doc@clinic.com", "pass")
        self.assertIn("Authentication failed", str(ctx.exception))

    def test_authenticate_defaults_missing_refresh_and_expires(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "tok",
            }
        }

        result = provider.authenticate("doc@clinic.com", "pass")

        self.assertEqual(result.refresh_token, "")
        self.assertEqual(result.expires_in, 3600)

    # --- sign_out ---

    def test_sign_out_success(self, mock_boto3: MagicMock) -> None:
        provider = self._make_provider(mock_boto3)

        provider.sign_out("valid-access-token")

        self.mock_client.global_sign_out.assert_called_once_with(
            AccessToken="valid-access-token"
        )

    def test_sign_out_invalid_token(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.global_sign_out.side_effect = _client_error(
            "NotAuthorizedException"
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.sign_out("expired-token")
        self.assertIn("Invalid or expired token", str(ctx.exception))

    def test_sign_out_unknown_error(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.global_sign_out.side_effect = _client_error(
            "InternalErrorException"
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.sign_out("some-token")
        self.assertIn("Sign-out failed", str(ctx.exception))

    # --- forgot_password ---

    def test_forgot_password_success(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)

        provider.forgot_password("doc@clinic.com")

        self.mock_client.forgot_password.assert_called_once_with(
            ClientId="client-abc",
            Username="doc@clinic.com",
        )

    def test_forgot_password_user_not_found_silent(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.forgot_password.side_effect = _client_error(
            "UserNotFoundException"
        )

        # Should NOT raise -- silently returns to avoid revealing existence
        provider.forgot_password("ghost@clinic.com")

    def test_forgot_password_invalid_parameter_silent(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.forgot_password.side_effect = _client_error(
            "InvalidParameterException"
        )

        # Should NOT raise -- unverified user, still silent
        provider.forgot_password("unverified@clinic.com")

    def test_forgot_password_unknown_error(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.forgot_password.side_effect = _client_error(
            "LimitExceededException"
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.forgot_password("doc@clinic.com")
        self.assertIn("Password reset failed", str(ctx.exception))

    # --- confirm_forgot_password ---

    def test_confirm_forgot_password_success(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)

        provider.confirm_forgot_password(
            "doc@clinic.com", "123456", "NewP@ss1!"
        )

        self.mock_client.confirm_forgot_password.assert_called_once_with(
            ClientId="client-abc",
            Username="doc@clinic.com",
            ConfirmationCode="123456",
            Password="NewP@ss1!",
        )

    def test_confirm_forgot_password_code_mismatch(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.confirm_forgot_password.side_effect = (
            _client_error("CodeMismatchException")
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.confirm_forgot_password(
                "doc@clinic.com", "wrong", "NewP@ss1!"
            )
        self.assertIn(
            "Invalid or expired confirmation code",
            str(ctx.exception),
        )

    def test_confirm_forgot_password_expired_code(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.confirm_forgot_password.side_effect = (
            _client_error("ExpiredCodeException")
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.confirm_forgot_password(
                "doc@clinic.com", "old-code", "NewP@ss1!"
            )
        self.assertIn(
            "Invalid or expired confirmation code",
            str(ctx.exception),
        )

    def test_confirm_forgot_password_user_not_found(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.confirm_forgot_password.side_effect = (
            _client_error("UserNotFoundException")
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.confirm_forgot_password(
                "ghost@clinic.com", "123456", "NewP@ss1!"
            )
        self.assertIn(
            "Invalid or expired confirmation code",
            str(ctx.exception),
        )

    def test_confirm_forgot_password_unknown_error(
        self, mock_boto3: MagicMock
    ) -> None:
        provider = self._make_provider(mock_boto3)
        self.mock_client.confirm_forgot_password.side_effect = (
            _client_error("InternalErrorException")
        )

        with self.assertRaises(AuthenticationError) as ctx:
            provider.confirm_forgot_password(
                "doc@clinic.com", "123456", "NewP@ss1!"
            )
        self.assertIn(
            "Password confirmation failed",
            str(ctx.exception),
        )


if __name__ == "__main__":
    unittest.main()
