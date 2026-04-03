"""Cognito authentication provider adapter."""

import boto3
import httpx
from botocore.exceptions import ClientError
from jose import JWTError, jwt

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
        self._jwks: dict | None = None
        self._region = (
            user_pool_id.split("_")[0] if "_" in user_pool_id else "us-east-1"
        )
        self._issuer = (
            f"https://cognito-idp.{self._region}.amazonaws.com/{user_pool_id}"
        )

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
            raise AuthenticationError(
                "Sign-out failed."
            ) from exc

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
                return
            if error_code == "InvalidParameterException":
                return
            raise AuthenticationError(
                "Password reset failed."
            ) from exc

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
            raise AuthenticationError(
                "Password confirmation failed."
            ) from exc

    def _get_jwks(self) -> dict:
        """Fetch and cache the Cognito JWKS key set."""
        if self._jwks is None:
            jwks_url = f"{self._issuer}/.well-known/jwks.json"
            response = httpx.get(jwks_url, timeout=5.0)
            response.raise_for_status()
            self._jwks = response.json()
        return self._jwks

    def validate_ws_token(self, token: str) -> dict:
        """Validate a WebSocket JWT and return identity claims."""
        if not token or not token.strip():
            raise AuthenticationError("Token must not be empty.")

        try:
            unverified_header = jwt.get_unverified_header(token)
        except JWTError as exc:
            raise AuthenticationError("Malformed token.") from exc

        kid = unverified_header.get("kid")
        jwks = self._get_jwks()

        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = key
                break

        if not rsa_key:
            raise AuthenticationError("Token signing key not found.")

        try:
            claims = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=self._issuer,
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError("Token has expired.") from exc
        except JWTError as exc:
            raise AuthenticationError(
                f"Token validation failed: {exc}"
            ) from exc

        doctor_id = claims.get("custom:doctor_id", "")
        clinic_id = claims.get("custom:clinic_id", "")

        if not doctor_id:
            raise AuthenticationError(
                "Token missing required claim: doctor_id."
            )
        if not clinic_id:
            raise AuthenticationError(
                "Token missing required claim: clinic_id."
            )

        return {
            "sub": claims.get("sub", ""),
            "doctor_id": doctor_id,
            "clinic_id": clinic_id,
        }
