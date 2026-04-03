"""Tests for container wiring completeness."""

import dataclasses
import os
from unittest.mock import MagicMock, patch

import pytest

from deskai.container import Container, build_container
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.event_publisher import EventPublisher
from deskai.ports.export_generator import ExportGenerator
from deskai.ports.llm_provider import LLMProvider
from deskai.ports.ui_config_assembler import UiConfigAssembler


# ---------------------------------------------------------------------------
# Structural checks (from main) — verify Container dataclass shape
# ---------------------------------------------------------------------------


class TestContainerFields:
    """Every port declared in the domain must be a field on Container."""

    def test_container_has_artifact_repo(self):
        field_names = {f.name for f in dataclasses.fields(Container)}
        assert "artifact_repo" in field_names

    def test_container_has_event_publisher(self):
        field_names = {f.name for f in dataclasses.fields(Container)}
        assert "event_publisher" in field_names

    def test_container_has_export_generator(self):
        field_names = {f.name for f in dataclasses.fields(Container)}
        assert "export_generator" in field_names

    def test_container_has_llm_provider(self):
        field_names = {f.name for f in dataclasses.fields(Container)}
        assert "llm_provider" in field_names

    def test_container_has_ui_config_assembler(self):
        field_names = {f.name for f in dataclasses.fields(Container)}
        assert "ui_config_assembler" in field_names

    def test_all_port_fields_are_typed(self):
        hints = {f.name: f.type for f in dataclasses.fields(Container)}
        assert hints.get("artifact_repo") is ArtifactRepository
        assert hints.get("event_publisher") is EventPublisher
        assert hints.get("export_generator") is ExportGenerator
        assert hints.get("llm_provider") is LLMProvider
        assert hints.get("ui_config_assembler") is UiConfigAssembler


# ---------------------------------------------------------------------------
# Runtime wiring checks (from branch) — verify build_container() actually
# creates instances that satisfy the port contracts.
# ---------------------------------------------------------------------------

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


@patch.dict(os.environ, _ENV, clear=False)
class TestContainerRuntimeWiring:
    """build_container() must wire real adapters that satisfy each port."""

    def test_artifact_repo(self):
        assert isinstance(_build().artifact_repo, ArtifactRepository)

    def test_event_publisher(self):
        assert isinstance(_build().event_publisher, EventPublisher)

    def test_export_generator(self):
        assert isinstance(_build().export_generator, ExportGenerator)

    def test_llm_provider(self):
        assert isinstance(_build().llm_provider, LLMProvider)

    def test_ui_config_assembler(self):
        assert isinstance(_build().ui_config_assembler, UiConfigAssembler)
