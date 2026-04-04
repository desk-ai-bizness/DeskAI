"""Tests for SecretsManagerClient — AWS Secrets Manager adapter."""

import json
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from deskai.adapters.secrets.secrets_manager import SecretsManagerClient


class TestSecretsManagerGetSecret(unittest.TestCase):
    """SecretsManagerClient.get_secret must parse SecretString JSON."""

    def setUp(self) -> None:
        self.mock_sm = MagicMock(name="secretsmanager-client")
        patcher = patch("deskai.adapters.secrets.secrets_manager.boto3")
        self.mock_boto3 = patcher.start()
        self.mock_boto3.client.return_value = self.mock_sm
        self.addCleanup(patcher.stop)
        self.client = SecretsManagerClient(region_name="us-east-1")

    def test_returns_parsed_dict_from_secret_string(self) -> None:
        secret_data = {"api_key": "sk-test-123", "model": "claude-sonnet-4-20250514"}
        self.mock_sm.get_secret_value.return_value = {
            "SecretString": json.dumps(secret_data),
        }

        result = self.client.get_secret("deskai/llm-api-key")

        self.assertEqual(result, secret_data)

    def test_passes_correct_secret_id_to_boto3(self) -> None:
        self.mock_sm.get_secret_value.return_value = {
            "SecretString": json.dumps({"key": "value"}),
        }

        self.client.get_secret("my/secret/name")

        self.mock_sm.get_secret_value.assert_called_once_with(SecretId="my/secret/name")

    def test_raises_on_missing_secret(self) -> None:
        self.mock_sm.get_secret_value.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Secret not found",
                }
            },
            "GetSecretValue",
        )

        with self.assertRaises(ClientError):
            self.client.get_secret("nonexistent/secret")

    def test_raises_on_malformed_json_in_secret_string(self) -> None:
        self.mock_sm.get_secret_value.return_value = {
            "SecretString": "not-valid-json{{{",
        }

        with self.assertRaises(json.JSONDecodeError):
            self.client.get_secret("bad/secret")


class TestSecretsManagerInit(unittest.TestCase):
    """SecretsManagerClient must pass region_name to boto3.client."""

    @patch("deskai.adapters.secrets.secrets_manager.boto3")
    def test_uses_provided_region(self, mock_boto3: MagicMock) -> None:
        SecretsManagerClient(region_name="eu-west-1")

        mock_boto3.client.assert_called_once_with("secretsmanager", region_name="eu-west-1")

    @patch("deskai.adapters.secrets.secrets_manager.boto3")
    def test_defaults_to_us_east_1(self, mock_boto3: MagicMock) -> None:
        SecretsManagerClient()

        mock_boto3.client.assert_called_once_with("secretsmanager", region_name="us-east-1")


if __name__ == "__main__":
    unittest.main()
