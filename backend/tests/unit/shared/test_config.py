"""Unit tests for environment-aware settings loading."""

import os
import unittest

from deskai.shared.config import (
    _PROD_REQUIRED_VARS,
    _is_strict_environment,
    load_settings,
)
from deskai.shared.errors import ConfigurationError


class IsStrictEnvironmentTest(unittest.TestCase):
    def test_prod_is_strict(self) -> None:
        self.assertTrue(_is_strict_environment("prod"))

    def test_staging_is_strict(self) -> None:
        self.assertTrue(_is_strict_environment("staging"))

    def test_dev_is_not_strict(self) -> None:
        self.assertFalse(_is_strict_environment("dev"))

    def test_test_is_not_strict(self) -> None:
        self.assertFalse(_is_strict_environment("test"))

    def test_empty_is_not_strict(self) -> None:
        self.assertFalse(_is_strict_environment(""))


class ProdRequiredVarsRegistryTest(unittest.TestCase):
    EXPECTED_REQUIRED = {
        "DESKAI_DYNAMODB_TABLE",
        "DESKAI_ARTIFACTS_BUCKET",
        "DESKAI_ELEVENLABS_SECRET_NAME",
        "DESKAI_CLAUDE_SECRET_NAME",
        "DESKAI_COGNITO_CLIENT_SECRET_NAME",
        "DESKAI_COGNITO_USER_POOL_ID",
        "DESKAI_COGNITO_CLIENT_ID",
        "DESKAI_WEBSOCKET_URL",
    }

    def test_all_critical_vars_are_registered(self) -> None:
        self.assertEqual(set(_PROD_REQUIRED_VARS), self.EXPECTED_REQUIRED)


class LoadSettingsDevTest(unittest.TestCase):
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
