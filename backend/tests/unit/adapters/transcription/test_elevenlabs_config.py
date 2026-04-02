"""Unit tests for ElevenLabs config loading."""

import json
import unittest
from unittest.mock import MagicMock, patch

from deskai.adapters.transcription.elevenlabs_config import (
    ElevenLabsConfig,
    load_elevenlabs_config,
)


class ElevenLabsConfigTest(unittest.TestCase):
    """Tests for ElevenLabsConfig dataclass."""

    def test_config_creation_with_all_fields(self) -> None:
        config = ElevenLabsConfig(
            api_key="test-key",
            ws_endpoint="wss://api.elevenlabs.io/v1/speech-to-text/ws",
            model="scribe_v2",
            language="pt",
            timeout_seconds=30,
        )

        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(
            config.ws_endpoint,
            "wss://api.elevenlabs.io/v1/speech-to-text/ws",
        )
        self.assertEqual(config.model, "scribe_v2")
        self.assertEqual(config.language, "pt")
        self.assertEqual(config.timeout_seconds, 30)

    def test_config_default_values(self) -> None:
        config = ElevenLabsConfig(api_key="test-key")

        self.assertEqual(
            config.ws_endpoint,
            "wss://api.elevenlabs.io/v1/speech-to-text/ws",
        )
        self.assertEqual(config.model, "scribe_v2")
        self.assertEqual(config.language, "pt")
        self.assertEqual(config.timeout_seconds, 30)

    def test_config_http_endpoint_derived_from_ws(self) -> None:
        config = ElevenLabsConfig(api_key="test-key")

        self.assertEqual(
            config.http_endpoint,
            "https://api.elevenlabs.io/v1/speech-to-text",
        )

    def test_config_is_frozen(self) -> None:
        config = ElevenLabsConfig(api_key="test-key")

        with self.assertRaises(AttributeError):
            config.api_key = "new-key"  # type: ignore[misc]


class LoadElevenLabsConfigTest(unittest.TestCase):
    """Tests for load_elevenlabs_config from Secrets Manager."""

    @patch("deskai.adapters.transcription.elevenlabs_config.boto3")
    def test_load_config_from_secrets_manager(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"elevenlabs_api_key": "secret-key-from-sm"})
        }

        config = load_elevenlabs_config(secret_name="deskai/dev/elevenlabs")

        self.assertIsInstance(config, ElevenLabsConfig)
        self.assertEqual(config.api_key, "secret-key-from-sm")
        mock_client.get_secret_value.assert_called_once_with(SecretId="deskai/dev/elevenlabs")

    @patch("deskai.adapters.transcription.elevenlabs_config.boto3")
    def test_load_config_uses_default_model_and_language(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"elevenlabs_api_key": "some-key"})
        }

        config = load_elevenlabs_config(secret_name="deskai/dev/elevenlabs")

        self.assertEqual(config.model, "scribe_v2")
        self.assertEqual(config.language, "pt")

    @patch("deskai.adapters.transcription.elevenlabs_config.boto3")
    def test_load_config_missing_key_raises(self, mock_boto3: MagicMock) -> None:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"other_key": "value"})
        }

        with self.assertRaises(KeyError):
            load_elevenlabs_config(secret_name="deskai/dev/elevenlabs")

    @patch("deskai.adapters.transcription.elevenlabs_config.boto3")
    def test_load_config_boto_client_error_propagates(self, mock_boto3: MagicMock) -> None:
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "not found",
                }
            },
            "GetSecretValue",
        )

        with self.assertRaises(ClientError):
            load_elevenlabs_config(secret_name="deskai/dev/elevenlabs")


if __name__ == "__main__":
    unittest.main()
