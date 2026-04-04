"""AWS Secrets Manager client adapter."""

import json
from typing import Any

import boto3


class SecretsManagerClient:
    """Fetch secrets from AWS Secrets Manager."""

    def __init__(self, region_name: str = "us-east-1") -> None:
        self._client = boto3.client("secretsmanager", region_name=region_name)

    def get_secret(self, secret_name: str) -> dict[str, Any]:
        """Retrieve and parse a JSON secret by name.

        Args:
            secret_name: The ARN or friendly name of the secret.

        Returns:
            Parsed secret payload as a dict.

        Raises:
            botocore.exceptions.ClientError: If the secret does not exist
                or cannot be accessed.
            json.JSONDecodeError: If the SecretString is not valid JSON.
        """
        response = self._client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
