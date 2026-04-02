"""Unit tests for shared utility modules."""

import os
import unittest
from unittest.mock import patch

from deskai.shared.config import (
    DEFAULT_ARTIFACTS_BUCKET,
    DEFAULT_DYNAMODB_TABLE,
    DEFAULT_UI_CONFIG_KEY,
    load_settings,
)
from deskai.shared.errors import ConfigurationError, DeskAIError
from deskai.shared.identifiers import new_uuid
from deskai.shared.time import utc_now_iso


class NewUuidTest(unittest.TestCase):
    def test_returns_string(self) -> None:
        result = new_uuid()
        self.assertIsInstance(result, str)

    def test_returns_valid_uuid_format(self) -> None:
        result = new_uuid()
        parts = result.split("-")
        self.assertEqual(len(parts), 5)

    def test_uniqueness(self) -> None:
        a = new_uuid()
        b = new_uuid()
        self.assertNotEqual(a, b)


class UtcNowIsoTest(unittest.TestCase):
    def test_returns_string(self) -> None:
        result = utc_now_iso()
        self.assertIsInstance(result, str)

    def test_contains_utc_indicator(self) -> None:
        result = utc_now_iso()
        self.assertTrue(
            result.endswith("+00:00") or result.endswith("Z"),
            f"Expected UTC suffix, got: {result}",
        )

    def test_contains_date_and_time_separator(self) -> None:
        result = utc_now_iso()
        self.assertIn("T", result)


class ErrorHierarchyTest(unittest.TestCase):
    def test_deskai_error_is_exception(self) -> None:
        self.assertTrue(issubclass(DeskAIError, Exception))

    def test_configuration_error_inherits_deskai_error(
        self,
    ) -> None:
        self.assertTrue(
            issubclass(ConfigurationError, DeskAIError)
        )

    def test_deskai_error_is_catchable(self) -> None:
        with self.assertRaises(DeskAIError):
            raise DeskAIError("test")

    def test_configuration_error_caught_as_deskai_error(
        self,
    ) -> None:
        with self.assertRaises(DeskAIError):
            raise ConfigurationError("missing config")


class GetLoggerTest(unittest.TestCase):
    def test_returns_named_logger(self) -> None:
        from deskai.shared.logging import get_logger

        logger = get_logger()
        self.assertIsNotNone(logger)

    def test_returns_same_instance(self) -> None:
        from deskai.shared.logging import get_logger

        a = get_logger()
        b = get_logger()
        self.assertIs(a, b)


class LoadSettingsDefaultsTest(unittest.TestCase):
    def test_default_environment_is_dev(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("DESKAI_")
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()
        self.assertEqual(settings.environment, "dev")

    def test_default_contract_version(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("DESKAI_")
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()
        self.assertEqual(settings.contract_version, "v1")

    def test_default_dynamodb_table(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("DESKAI_")
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()
        self.assertEqual(
            settings.dynamodb_table, DEFAULT_DYNAMODB_TABLE
        )

    def test_default_artifacts_bucket(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("DESKAI_")
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()
        self.assertEqual(
            settings.artifacts_bucket, DEFAULT_ARTIFACTS_BUCKET
        )

    def test_default_ui_config_key(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("DESKAI_")
        }
        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()
        self.assertEqual(
            settings.ui_config_key, DEFAULT_UI_CONFIG_KEY
        )

    def test_settings_is_frozen(self) -> None:
        settings = load_settings()
        with self.assertRaises(AttributeError):
            settings.environment = "prod"  # type: ignore[misc]


class LoadSettingsFromEnvTest(unittest.TestCase):
    def test_overrides_from_env_vars(self) -> None:
        custom_env = {
            "DESKAI_ENV": "prod",
            "DESKAI_CONTRACT_VERSION": "v2",
            "DESKAI_DYNAMODB_TABLE": "prod-table",
            "DESKAI_ARTIFACTS_BUCKET": "prod-bucket",
            "DESKAI_UI_CONFIG_KEY": "CONFIG#prod",
            "DESKAI_ELEVENLABS_SECRET_NAME": "prod/elevenlabs",
            "DESKAI_CLAUDE_SECRET_NAME": "prod/claude",
            "DESKAI_COGNITO_CLIENT_SECRET_NAME": "prod/cognito",
            "DESKAI_COGNITO_USER_POOL_ID": "us-east-1_abc",
            "DESKAI_COGNITO_CLIENT_ID": "client-id-123",
        }
        with patch.dict(os.environ, custom_env, clear=True):
            settings = load_settings()

        self.assertEqual(settings.environment, "prod")
        self.assertEqual(settings.contract_version, "v2")
        self.assertEqual(settings.dynamodb_table, "prod-table")
        self.assertEqual(settings.artifacts_bucket, "prod-bucket")
        self.assertEqual(settings.ui_config_key, "CONFIG#prod")
        self.assertEqual(
            settings.elevenlabs_secret_name, "prod/elevenlabs"
        )
        self.assertEqual(
            settings.claude_secret_name, "prod/claude"
        )
        self.assertEqual(
            settings.cognito_secret_name, "prod/cognito"
        )
        self.assertEqual(
            settings.cognito_user_pool_id, "us-east-1_abc"
        )
        self.assertEqual(
            settings.cognito_client_id, "client-id-123"
        )

    def test_partial_env_uses_defaults_for_rest(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("DESKAI_")
        }
        env["DESKAI_ENV"] = "staging"
        with patch.dict(os.environ, env, clear=True):
            settings = load_settings()

        self.assertEqual(settings.environment, "staging")
        self.assertEqual(settings.contract_version, "v1")
        self.assertEqual(
            settings.dynamodb_table, DEFAULT_DYNAMODB_TABLE
        )


if __name__ == "__main__":
    unittest.main()
