"""Unit tests for environment-aware configuration safety."""

import os
import unittest
from unittest.mock import patch

import pytest

from deskai.shared.config import (
    _PROD_REQUIRED_VARS,
    _is_strict_environment,
    _require_env_vars,
    load_settings,
)
from deskai.shared.errors import ConfigurationError

# ---------------------------------------------------------------------------
# Unit tests for helper functions (branch — pytest style)
# ---------------------------------------------------------------------------


class TestIsStrictEnvironment:
    """Validate strict-environment detection."""

    def test_prod_is_strict(self):
        assert _is_strict_environment("prod") is True

    def test_staging_is_strict(self):
        assert _is_strict_environment("staging") is True

    def test_dev_is_not_strict(self):
        assert _is_strict_environment("dev") is False

    def test_test_is_not_strict(self):
        assert _is_strict_environment("test") is False

    def test_empty_string_is_not_strict(self):
        assert _is_strict_environment("") is False


class TestProdRequiredVars:
    """Validate the required-vars registry."""

    def test_registry_is_frozen(self):
        assert isinstance(_PROD_REQUIRED_VARS, frozenset)

    def test_registry_contains_critical_vars(self):
        expected = {
            "DESKAI_DYNAMODB_TABLE",
            "DESKAI_ARTIFACTS_BUCKET",
            "DESKAI_ELEVENLABS_SECRET_NAME",
            "DESKAI_CLAUDE_SECRET_NAME",
            "DESKAI_COGNITO_CLIENT_SECRET_NAME",
            "DESKAI_COGNITO_USER_POOL_ID",
            "DESKAI_COGNITO_CLIENT_ID",
            "DESKAI_WEBSOCKET_URL",
        }
        assert _PROD_REQUIRED_VARS == expected


class TestRequireEnvVars:
    """Validate _require_env_vars enforcement logic."""

    def test_dev_never_raises(self):
        _require_env_vars("dev")

    def test_test_never_raises(self):
        _require_env_vars("test")

    @patch.dict(os.environ, {}, clear=True)
    def test_prod_raises_when_all_missing(self):
        with pytest.raises(
            ConfigurationError,
            match="Missing required environment variables for 'prod'",
        ):
            _require_env_vars("prod")

    @patch.dict(
        os.environ,
        {var: "value" for var in _PROD_REQUIRED_VARS},
        clear=True,
    )
    def test_prod_passes_when_all_set(self):
        _require_env_vars("prod")

    @patch.dict(
        os.environ,
        {var: "value" for var in _PROD_REQUIRED_VARS},
        clear=True,
    )
    def test_staging_passes_when_all_set(self):
        _require_env_vars("staging")

    @patch.dict(os.environ, {"DESKAI_DYNAMODB_TABLE": ""}, clear=True)
    def test_empty_string_treated_as_missing(self):
        with pytest.raises(ConfigurationError):
            _require_env_vars("prod")

    @patch.dict(os.environ, {}, clear=True)
    def test_error_lists_all_missing_vars(self):
        with pytest.raises(ConfigurationError) as exc_info:
            _require_env_vars("prod")
        message = str(exc_info.value)
        for var in _PROD_REQUIRED_VARS:
            assert var in message


# ---------------------------------------------------------------------------
# Integration tests for load_settings (main — thorough env management)
# ---------------------------------------------------------------------------


class LoadSettingsDevTest(unittest.TestCase):
    """In dev mode, defaults are silently used."""

    def setUp(self) -> None:
        self._saved = {}
        for key in list(os.environ):
            if key.startswith("DESKAI_"):
                self._saved[key] = os.environ.pop(key)

    def tearDown(self) -> None:
        for key in list(os.environ):
            if key.startswith("DESKAI_"):
                del os.environ[key]
        os.environ.update(self._saved)

    def test_dev_loads_defaults_without_error(self) -> None:
        settings = load_settings()
        self.assertEqual(settings.environment, "dev")
        self.assertEqual(settings.websocket_url, "wss://localhost:3001")
        self.assertEqual(settings.dynamodb_table, "deskai-dev-consultation-records")

    def test_dev_uses_provided_env_var_over_default(self) -> None:
        os.environ["DESKAI_WEBSOCKET_URL"] = "wss://prod.example.com"
        settings = load_settings()
        self.assertEqual(settings.websocket_url, "wss://prod.example.com")


class LoadSettingsProdTest(unittest.TestCase):
    """In prod mode, missing required vars raise ConfigurationError."""

    def setUp(self) -> None:
        self._saved = {}
        for key in list(os.environ):
            if key.startswith("DESKAI_"):
                self._saved[key] = os.environ.pop(key)

    def tearDown(self) -> None:
        for key in list(os.environ):
            if key.startswith("DESKAI_"):
                del os.environ[key]
        os.environ.update(self._saved)

    def _set_all_required(self) -> None:
        os.environ["DESKAI_ENV"] = "prod"
        os.environ["DESKAI_DYNAMODB_TABLE"] = "deskai-prod-records"
        os.environ["DESKAI_ARTIFACTS_BUCKET"] = "deskai-prod-artifacts"
        os.environ["DESKAI_ELEVENLABS_SECRET_NAME"] = "deskai/prod/elevenlabs"
        os.environ["DESKAI_CLAUDE_SECRET_NAME"] = "deskai/prod/claude"
        os.environ["DESKAI_COGNITO_CLIENT_SECRET_NAME"] = "deskai/prod/cognito"
        os.environ["DESKAI_COGNITO_USER_POOL_ID"] = "us-east-1_ABCDEF"
        os.environ["DESKAI_COGNITO_CLIENT_ID"] = "prod-client-id"
        os.environ["DESKAI_WEBSOCKET_URL"] = "wss://ws.deskai.com.br/prod"

    def test_prod_with_all_vars_set_succeeds(self) -> None:
        self._set_all_required()
        settings = load_settings()
        self.assertEqual(settings.environment, "prod")
        self.assertEqual(settings.dynamodb_table, "deskai-prod-records")

    def test_prod_missing_dynamodb_table_raises(self) -> None:
        self._set_all_required()
        del os.environ["DESKAI_DYNAMODB_TABLE"]
        with self.assertRaises(ConfigurationError) as ctx:
            load_settings()
        self.assertIn("DESKAI_DYNAMODB_TABLE", str(ctx.exception))

    def test_prod_missing_websocket_url_raises(self) -> None:
        self._set_all_required()
        del os.environ["DESKAI_WEBSOCKET_URL"]
        with self.assertRaises(ConfigurationError) as ctx:
            load_settings()
        self.assertIn("DESKAI_WEBSOCKET_URL", str(ctx.exception))

    def test_prod_missing_cognito_user_pool_id_raises(self) -> None:
        self._set_all_required()
        del os.environ["DESKAI_COGNITO_USER_POOL_ID"]
        with self.assertRaises(ConfigurationError) as ctx:
            load_settings()
        self.assertIn("DESKAI_COGNITO_USER_POOL_ID", str(ctx.exception))

    def test_prod_missing_multiple_vars_lists_all(self) -> None:
        self._set_all_required()
        del os.environ["DESKAI_DYNAMODB_TABLE"]
        del os.environ["DESKAI_WEBSOCKET_URL"]
        with self.assertRaises(ConfigurationError) as ctx:
            load_settings()
        message = str(ctx.exception)
        self.assertIn("DESKAI_DYNAMODB_TABLE", message)
        self.assertIn("DESKAI_WEBSOCKET_URL", message)

    def test_staging_also_enforces_required_vars(self) -> None:
        self._set_all_required()
        os.environ["DESKAI_ENV"] = "staging"
        del os.environ["DESKAI_WEBSOCKET_URL"]
        with self.assertRaises(ConfigurationError) as ctx:
            load_settings()
        self.assertIn("DESKAI_WEBSOCKET_URL", str(ctx.exception))

    def test_prod_empty_string_counts_as_missing(self) -> None:
        self._set_all_required()
        os.environ["DESKAI_COGNITO_USER_POOL_ID"] = ""
        with self.assertRaises(ConfigurationError) as ctx:
            load_settings()
        self.assertIn("DESKAI_COGNITO_USER_POOL_ID", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
