"""Tests for container wiring completeness."""

import dataclasses

from deskai.container import Container
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.event_publisher import EventPublisher
from deskai.ports.export_generator import ExportGenerator
from deskai.ports.llm_provider import LLMProvider
from deskai.ports.ui_config_assembler import UiConfigAssembler


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
