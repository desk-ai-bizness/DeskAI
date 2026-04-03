"""Unit tests for the dependency container."""

import os
import unittest
from unittest.mock import MagicMock, patch

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
from deskai.container import Container, build_container

_REQUIRED_ENV = {
    "DESKAI_COGNITO_USER_POOL_ID": "us-east-1_TestPool",
    "DESKAI_COGNITO_CLIENT_ID": "test-client-id",
    "AWS_DEFAULT_REGION": "us-east-1",
}


_SECRET_VALUE = '{"elevenlabs_api_key": "test-key-123"}'


def _build_with_mocked_boto():
    """Build container with boto3 mocked at the adapter level."""
    with (
        patch("deskai.adapters.auth.cognito_provider.boto3") as mock_boto3,
        patch(
            "deskai.adapters.persistence.base_repository.boto3"
        ) as mock_dynamo,
        patch(
            "deskai.adapters.transcription.elevenlabs_config.boto3"
        ) as mock_secrets,
        patch("deskai.adapters.storage.s3_client.boto3") as mock_s3,
    ):
        mock_boto3.client.return_value = MagicMock()
        mock_dynamo.resource.return_value.Table.return_value = MagicMock()
        mock_secrets.client.return_value.get_secret_value.return_value = {
            "SecretString": _SECRET_VALUE
        }
        mock_s3.client.return_value = MagicMock()
        return build_container()


class BuildContainerTest(unittest.TestCase):
    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_build_container_returns_container(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(container, Container)

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_authenticate_use_case(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(container.authenticate, AuthenticateUseCase)

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_sign_out_use_case(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(container.sign_out, SignOutUseCase)

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_get_current_user_use_case(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(container.get_current_user, GetCurrentUserUseCase)

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_forgot_password_use_case(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(container.forgot_password, ForgotPasswordUseCase)
        self.assertIsInstance(
            container.confirm_forgot_password, ConfirmForgotPasswordUseCase
        )

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_check_entitlements_use_case(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(
            container.check_entitlements, CheckEntitlementsUseCase
        )


if __name__ == "__main__":
    unittest.main()
