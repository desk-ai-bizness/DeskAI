"""Tests for CognitoAuthProvider.validate_ws_token."""

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from jose import jwt

from deskai.domain.auth.exceptions import AuthenticationError


def _generate_rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    import base64

    def _b64url(num, length):
        data = num.to_bytes(length, byteorder="big")
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    n = _b64url(public_numbers.n, 256)
    e = _b64url(public_numbers.e, 3)

    jwk = {"kty": "RSA", "kid": "test-kid-1", "use": "sig", "alg": "RS256", "n": n, "e": e}
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return jwk, pem


JWK, PRIVATE_PEM = _generate_rsa_keypair()
JWKS = {"keys": [JWK]}

POOL_ID = "us-east-1_TestPool"
CLIENT_ID = "test-client-id"
ISSUER = f"https://cognito-idp.us-east-1.amazonaws.com/{POOL_ID}"


def _make_token(claims_override=None, headers_override=None, exp_offset=3600):
    claims = {
        "sub": "user-uuid",
        "aud": CLIENT_ID,
        "iss": ISSUER,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_offset,
        "custom:doctor_id": "doc-1",
        "custom:clinic_id": "clinic-1",
    }
    if claims_override:
        claims.update(claims_override)
    headers = {"kid": "test-kid-1"}
    if headers_override:
        headers.update(headers_override)
    return jwt.encode(claims, PRIVATE_PEM, algorithm="RS256", headers=headers)


def _mock_httpx_get(url, **kwargs):
    resp = MagicMock()
    resp.json.return_value = JWKS
    resp.raise_for_status = MagicMock()
    return resp


@patch("deskai.adapters.auth.cognito_provider.boto3")
class TestValidateWsToken:
    """Test suite for validate_ws_token."""

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_valid_token(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        token = _make_token()
        result = provider.validate_ws_token(token)
        assert result["doctor_id"] == "doc-1"
        assert result["clinic_id"] == "clinic-1"
        assert result["sub"] == "user-uuid"

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_expired_token(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        token = _make_token(exp_offset=-3600)
        with pytest.raises(AuthenticationError):
            provider.validate_ws_token(token)

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_invalid_signature(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        _, other_pem = _generate_rsa_keypair()
        claims = {
            "sub": "x", "aud": CLIENT_ID, "iss": ISSUER,
            "iat": int(time.time()), "exp": int(time.time()) + 3600,
            "custom:doctor_id": "d", "custom:clinic_id": "c",
        }
        token = jwt.encode(claims, other_pem, algorithm="RS256", headers={"kid": "test-kid-1"})
        with pytest.raises(AuthenticationError):
            provider.validate_ws_token(token)

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_missing_doctor_id(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        token = _make_token(claims_override={"custom:doctor_id": ""})
        with pytest.raises(AuthenticationError, match="doctor_id"):
            provider.validate_ws_token(token)

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_missing_clinic_id(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        token = _make_token(claims_override={"custom:clinic_id": ""})
        with pytest.raises(AuthenticationError, match="clinic_id"):
            provider.validate_ws_token(token)

    def test_empty_token(self, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        with pytest.raises(AuthenticationError, match="empty"):
            provider.validate_ws_token("")

    def test_garbage_token(self, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        with pytest.raises(AuthenticationError, match="Malformed"):
            provider.validate_ws_token("not.a.jwt")

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_wrong_audience(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        token = _make_token(claims_override={"aud": "wrong-client"})
        with pytest.raises(AuthenticationError):
            provider.validate_ws_token(token)

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_wrong_issuer(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        token = _make_token(claims_override={"iss": "https://evil.example.com"})
        with pytest.raises(AuthenticationError):
            provider.validate_ws_token(token)

    @patch("deskai.adapters.auth.cognito_provider.httpx.get", side_effect=_mock_httpx_get)
    def test_jwks_cached(self, mock_get, mock_boto):
        from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
        provider = CognitoAuthProvider(POOL_ID, CLIENT_ID)
        token1 = _make_token()
        token2 = _make_token(claims_override={"sub": "other-user"})
        provider.validate_ws_token(token1)
        provider.validate_ws_token(token2)
        assert mock_get.call_count == 1
