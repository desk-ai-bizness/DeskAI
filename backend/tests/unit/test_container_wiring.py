"""Unit tests for container wiring of 4 newly added ports."""

import os
import unittest
from unittest.mock import MagicMock, patch

from deskai.container import build_container
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.event_publisher import EventPublisher
from deskai.ports.export_generator import ExportGenerator
from deskai.ports.llm_provider import LLMProvider
from deskai.ports.ui_config_assembler import UiConfigAssembler

_ENV = {
    "DESKAI_COGNITO_USER_POOL_ID": "us-east-1_TestPool",
    "DESKAI_COGNITO_CLIENT_ID": "test-client-id",
    "AWS_DEFAULT_REGION": "us-east-1",
}
_SECRET = '{"elevenlabs_api_key": "k"}'

def _build():
    with (
        patch("deskai.adapters.auth.cognito_provider.boto3") as b1,
        patch("deskai.adapters.persistence.dynamodb_doctor_repository.boto3") as b2,
        patch("deskai.adapters.transcription.elevenlabs_config.boto3") as b3,
        patch("deskai.adapters.storage.s3_client.boto3") as b4,
    ):
        b1.client.return_value = MagicMock()
        b2.resource.return_value.Table.return_value = MagicMock()
        b3.client.return_value.get_secret_value.return_value = {"SecretString": _SECRET}
        b4.client.return_value = MagicMock()
        return build_container()

class ContainerWiringTest(unittest.TestCase):
    @patch.dict(os.environ, _ENV, clear=False)
    def test_artifact_repo(self):
        c = _build()
        self.assertIsInstance(c.artifact_repo, ArtifactRepository)

    @patch.dict(os.environ, _ENV, clear=False)
    def test_event_publisher(self):
        c = _build()
        self.assertIsInstance(c.event_publisher, EventPublisher)

    @patch.dict(os.environ, _ENV, clear=False)
    def test_export_generator(self):
        c = _build()
        self.assertIsInstance(c.export_generator, ExportGenerator)

    @patch.dict(os.environ, _ENV, clear=False)
    def test_llm_provider(self):
        c = _build()
        self.assertIsInstance(c.llm_provider, LLMProvider)

    @patch.dict(os.environ, _ENV, clear=False)
    def test_ui_config_assembler(self):
        c = _build()
        self.assertIsInstance(c.ui_config_assembler, UiConfigAssembler)

if __name__ == "__main__":
    unittest.main()
