"""Unit tests for HTTP authentication handlers."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.auth.exceptions import AuthenticationError
from deskai.domain.auth.value_objects import Tokens
from deskai.handlers.http.auth_handler import (
    handle_confirm_forgot_password,
    handle_forgot_password,
    handle_login,
    handle_logout,
)


def _login_event(email: str = "", password: str = "") -> dict:
    body = {}
    if email:
        body["email"] = email
    if password:
        body["password"] = password
    return {"body": json.dumps(body)}


def _logout_event(token: str = "") -> dict:
    headers = {}
    if token:
        headers["authorization"] = f"Bearer {token}"
    return {"headers": headers}


def _forgot_event(email: str = "") -> dict:
    body = {}
    if email:
        body["email"] = email
    return {"body": json.dumps(body)}


def _confirm_forgot_event(
    email: str = "",
    code: str = "",
    new_password: str = "",
) -> dict:
    body = {}
    if email:
        body["email"] = email
    if code:
        body["confirmation_code"] = code
    if new_password:
        body["new_password"] = new_password
    return {"body": json.dumps(body)}


class HandleLoginTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()

    def test_handle_login_success(self) -> None:
        self.container.authenticate.execute.return_value = (
            Tokens(
                access_token="at",
                refresh_token="rt",
                expires_in=3600,
            )
        )
        event = _login_event("a@b.com", "secret")
        resp = handle_login(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["access_token"], "at")
        self.assertEqual(body["refresh_token"], "rt")
        self.assertEqual(body["expires_in"], 3600)

    def test_handle_login_missing_email(self) -> None:
        resp = handle_login(
            _login_event(password="secret"), self.container
        )
        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(
            body["error"]["code"], "validation_error"
        )

    def test_handle_login_missing_password(self) -> None:
        resp = handle_login(
            _login_event(email="a@b.com"), self.container
        )
        self.assertEqual(resp["statusCode"], 400)

    def test_handle_login_invalid_credentials(self) -> None:
        self.container.authenticate.execute.side_effect = (
            AuthenticationError("bad creds")
        )
        resp = handle_login(
            _login_event("a@b.com", "wrong"), self.container
        )
        self.assertEqual(resp["statusCode"], 401)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "unauthorized")


class HandleLogoutTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()

    def test_handle_logout_success(self) -> None:
        resp = handle_logout(
            _logout_event("valid-token"), self.container
        )
        self.assertEqual(resp["statusCode"], 204)
        self.container.sign_out.execute.assert_called_once_with(
            "valid-token"
        )

    def test_handle_logout_missing_token(self) -> None:
        resp = handle_logout(_logout_event(), self.container)
        self.assertEqual(resp["statusCode"], 401)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "unauthorized")


class HandleForgotPasswordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()

    def test_handle_forgot_password_success(self) -> None:
        resp = handle_forgot_password(
            _forgot_event("a@b.com"), self.container
        )
        self.assertEqual(resp["statusCode"], 200)
        self.container.forgot_password.execute.assert_called_once_with(
            "a@b.com"
        )

    def test_handle_forgot_password_missing_email(
        self,
    ) -> None:
        resp = handle_forgot_password(
            _forgot_event(), self.container
        )
        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(
            body["error"]["code"], "validation_error"
        )


class HandleConfirmForgotPasswordTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()

    def test_handle_confirm_forgot_password_success(
        self,
    ) -> None:
        resp = handle_confirm_forgot_password(
            _confirm_forgot_event("a@b.com", "123456", "new"),
            self.container,
        )
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertIn("Senha alterada", body["message"])

    def test_handle_confirm_forgot_password_missing_fields(
        self,
    ) -> None:
        resp = handle_confirm_forgot_password(
            _confirm_forgot_event(email="a@b.com"),
            self.container,
        )
        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(
            body["error"]["code"], "validation_error"
        )


if __name__ == "__main__":
    unittest.main()
