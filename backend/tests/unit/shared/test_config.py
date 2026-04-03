"""Unit tests for environment-aware configuration safety."""

import os
from unittest.mock import patch

import pytest

from deskai.shared.config import (
    _PROD_REQUIRED_VARS,
    _is_strict_environment,
    _require_env_vars,
    load_settings,
)
from deskai.shared.errors import ConfigurationError


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
    """Validate enforcement logic."""

    def test_dev_never_raises(self):
        _require_env_vars("dev")

    def test_test_never_raises(self):
        _require_env_vars("test")

    @patch.dict(os.environ, {}, clear=True)
    def test_prod_raises_when_all_missing(self):
        with pytest.raises(ConfigurationError, match="Missing required environment variables for 'prod'"):
            _require_env_vars("prod")

    @patch.dict(os.environ, {var: "value" for var in _PROD_REQUIRED_VARS}, clear=True)
    def test_prod_passes_when_all_set(self):
        _require_env_vars("prod")

    @patch.dict(os.environ, {var: "value" for var in _PROD_REQUIRED_VARS}, clear=True)
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


class TestLoadSettings:
    """Integration: load_settings respects environment mode."""

    def test_dev_loads_with_defaults(self):
        settings = load_settings()
        assert settings.environment == "dev"
        assert settings.dynamodb_table == "deskai-dev-consultation-records"

    @patch.dict(os.environ, {"DESKAI_ENV": "prod"}, clear=True)
    def test_prod_raises_without_required_vars(self):
        with pytest.raises(ConfigurationError):
            load_settings()
