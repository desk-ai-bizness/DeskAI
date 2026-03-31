"""Cognito authentication provider adapter."""

import boto3
from botocore.exceptions import ClientError

from deskai.domain.auth.exceptions import (
    AccountNotVerifiedError,
    AuthenticationError,
)
from deskai.domain.auth.value_objects import Tokens
from deskai.ports.auth_provider import AuthProvider
from deskai.shared.logging import get_logger

logger = get_logger()


class CognitoAuthProvider(AuthProvider):
    """Authenticate users via AWS Cognito user pool."""

    def __init__(
        self, user_pool_id: str, client_id: str
    ) -> None:
        self._user_pool_id = user_pool_id
        self._client_id = client_id
        self._client = boto3.client("cognito-idp")

    def authenticate(
        self, email: str, password: str
    ) -> Tokens:
        try:
            response = self._client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                },
                ClientId=self._client_id,
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get(
                "Code", ""
            )
            logger.info(
                "cognito_auth_failed",
                extra={"error_code": error_code},
            )
            if error_code == "NotAuthorizedException":
                raise AuthenticationError(
                    "Invalid email or password."
                ) from exc
            if error_code == "UserNotConfirmedException":
                raise AccountNotVerifiedError(
                    "Email has not been verified."
                ) from exc
            if error_code == "UserNotFoundException":
                raise AuthenticationError(
                    "Invalid email or password."
                ) from exc
            raise AuthenticationError(
                f"Authentication failed: {error_code}"
            ) from exc

        result = response["AuthenticationResult"]
        return Tokens(
            access_token=result["AccessToken"],
            refresh_token=result.get("RefreshToken", ""),
            expires_in=result.get("ExpiresIn", 3600),
        )

    def sign_out(self, access_token: str) -> None:
        try:
            self._client.global_sign_out(
                AccessToken=access_token
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get(
                "Code", ""
            )
            logger.warning(
                "cognito_sign_out_failed",
                extra={"error_code": error_code},
            )
            if error_code == "NotAuthorizedException":
                raise AuthenticationError(
                    "Invalid or expired token."
                ) from exc
            raise

    def forgot_password(self, email: str) -> None:
        try:
            self._client.forgot_password(
                ClientId=self._client_id,
                Username=email,
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get(
                "Code", ""
            )
            logger.info(
                "cognito_forgot_password",
                extra={"error_code": error_code},
            )
            if error_code == "UserNotFoundException":
                return  # Do not reveal whether the email exists
            if error_code == "InvalidParameterException":
                return  # Unverified users -- still do not reveal
            raise

    def confirm_forgot_password(
        self,
        email: str,
        confirmation_code: str,
        new_password: str,
    ) -> None:
        try:
            self._client.confirm_forgot_password(
                ClientId=self._client_id,
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password,
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get(
                "Code", ""
            )
            logger.info(
                "cognito_confirm_forgot_password_failed",
                extra={"error_code": error_code},
            )
            if error_code in (
                "CodeMismatchException",
                "ExpiredCodeException",
            ):
                raise AuthenticationError(
                    "Invalid or expired confirmation code."
                ) from exc
            if error_code == "UserNotFoundException":
                raise AuthenticationError(
                    "Invalid or expired confirmation code."
                ) from exc
            raise
