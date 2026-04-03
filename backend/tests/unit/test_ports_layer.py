"""Tests for ports layer: cognito rename, typed returns, stub ports, async ports."""

import inspect
import unittest
from abc import ABC
from typing import Any, get_type_hints

from deskai.domain.ai_pipeline.value_objects import StructuredOutput
from deskai.domain.config.value_objects import FeatureFlag
from deskai.domain.export.value_objects import ExportFormat, ExportResult
from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.value_objects import (
    FinalTranscript,
    SpeakerSegment,
    TranscriptionSessionInfo,
)
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.async_ai_pipeline import AsyncAIPipelinePort
from deskai.ports.async_transcription_provider import AsyncTranscriptionProvider
from deskai.ports.config_repository import ConfigRepository
from deskai.ports.doctor_repository import DoctorRepository
from deskai.ports.event_publisher import EventPublisher
from deskai.ports.export_generator import ExportGenerator
from deskai.ports.llm_provider import LLMProvider
from deskai.ports.storage_provider import StorageProvider
from deskai.ports.transcript_repository import TranscriptRepository
from deskai.ports.transcription_provider import TranscriptionProvider

# ── 1. Cognito rename ──────────────────────────────────────────────


class DoctorRepositoryRenameTest(unittest.TestCase):
    """Verify cognito_sub has been renamed to identity_provider_id."""

    def test_no_cognito_sub_in_doctor_repo(self):
        source = inspect.getsource(DoctorRepository)
        self.assertNotIn("cognito_sub", source)
        self.assertIn("identity_provider_id", source)

    def test_find_by_identity_provider_id_is_abstract(self):
        self.assertTrue(
            hasattr(DoctorRepository, "find_by_identity_provider_id")
        )
        method = DoctorRepository.find_by_identity_provider_id
        self.assertTrue(getattr(method, "__isabstractmethod__", False))


# ── 2. Typed return ports ──────────────────────────────────────────


class LLMProviderTypedReturnTest(unittest.TestCase):
    def test_returns_structured_output(self):
        hints = get_type_hints(LLMProvider.generate_structured_output)
        self.assertIs(hints["return"], StructuredOutput)


class TranscriptionProviderTypedReturnTest(unittest.TestCase):
    def test_start_returns_session_info(self):
        hints = get_type_hints(TranscriptionProvider.start_realtime_session)
        self.assertIs(hints["return"], TranscriptionSessionInfo)

    def test_finish_returns_session_info(self):
        hints = get_type_hints(TranscriptionProvider.finish_realtime_session)
        self.assertIs(hints["return"], TranscriptionSessionInfo)

    def test_fetch_returns_final_transcript(self):
        hints = get_type_hints(TranscriptionProvider.fetch_final_transcript)
        self.assertIs(hints["return"], FinalTranscript)


class TranscriptRepositoryTypedReturnTest(unittest.TestCase):
    def test_save_normalized_accepts_entity(self):
        hints = get_type_hints(TranscriptRepository.save_normalized_transcript)
        self.assertIs(hints["normalized"], NormalizedTranscript)

    def test_get_normalized_returns_optional_entity(self):
        hints = get_type_hints(TranscriptRepository.get_normalized_transcript)
        ret = hints["return"]
        self.assertIn(NormalizedTranscript, ret.__args__)

    def test_save_raw_uses_typed_dict(self):
        hints = get_type_hints(TranscriptRepository.save_raw_transcript)
        self.assertEqual(hints["raw_response"], dict[str, Any])


class ArtifactRepositoryTypedReturnTest(unittest.TestCase):
    def test_save_uses_typed_dict(self):
        hints = get_type_hints(ArtifactRepository.save_artifact)
        self.assertEqual(hints["data"], dict[str, Any])

    def test_get_returns_typed_dict_or_none(self):
        hints = get_type_hints(ArtifactRepository.get_artifact)
        self.assertIn(type(None), hints["return"].__args__)


# ── 3. Fleshed-out stub ports ──────────────────────────────────────


def _abstract_methods(cls: type) -> set[str]:
    return {
        name
        for name, method in inspect.getmembers(cls)
        if getattr(method, "__isabstractmethod__", False)
    }


class ConfigRepositoryPortTest(unittest.TestCase):
    def test_is_abstract(self):
        self.assertTrue(issubclass(ConfigRepository, ABC))

    def test_has_expected_methods(self):
        methods = _abstract_methods(ConfigRepository)
        self.assertEqual(
            methods,
            {"get_feature_flag", "list_feature_flags", "get_config_value"},
        )


class EventPublisherPortTest(unittest.TestCase):
    def test_has_expected_methods(self):
        methods = _abstract_methods(EventPublisher)
        self.assertEqual(methods, {"publish", "publish_batch"})


class ExportGeneratorPortTest(unittest.TestCase):
    def test_has_expected_methods(self):
        methods = _abstract_methods(ExportGenerator)
        self.assertEqual(methods, {"generate"})


class StorageProviderPortTest(unittest.TestCase):
    def test_has_expected_methods(self):
        methods = _abstract_methods(StorageProvider)
        self.assertEqual(
            methods,
            {"put", "get", "exists", "delete", "generate_presigned_url"},
        )


# ── 4. Async ports ────────────────────────────────────────────────


class AsyncTranscriptionProviderTest(unittest.TestCase):
    def test_is_abstract(self):
        self.assertTrue(issubclass(AsyncTranscriptionProvider, ABC))

    def test_has_expected_methods(self):
        methods = _abstract_methods(AsyncTranscriptionProvider)
        self.assertEqual(
            methods,
            {
                "start_session",
                "send_audio_chunk",
                "receive_partials",
                "finish_session",
                "get_session_state",
            },
        )

    def test_methods_are_async(self):
        for name in [
            "start_session",
            "send_audio_chunk",
            "receive_partials",
            "finish_session",
            "get_session_state",
        ]:
            method = getattr(AsyncTranscriptionProvider, name)
            self.assertTrue(
                inspect.iscoroutinefunction(method),
                f"{name} should be async",
            )


class AsyncAIPipelinePortTest(unittest.TestCase):
    def test_is_abstract(self):
        self.assertTrue(issubclass(AsyncAIPipelinePort, ABC))

    def test_has_expected_methods(self):
        methods = _abstract_methods(AsyncAIPipelinePort)
        self.assertEqual(
            methods, {"generate_streaming", "generate_structured"}
        )

    def test_methods_are_async(self):
        for name in ["generate_streaming", "generate_structured"]:
            method = getattr(AsyncAIPipelinePort, name)
            self.assertTrue(
                inspect.iscoroutinefunction(method),
                f"{name} should be async",
            )


# ── 5. Domain VO smoke tests ──────────────────────────────────────


class StructuredOutputSmokeTest(unittest.TestCase):
    def test_creation(self):
        vo = StructuredOutput(task="soap", payload={"text": "hello"})
        self.assertEqual(vo.task, "soap")
        self.assertEqual(vo.payload, {"text": "hello"})

    def test_immutable(self):
        vo = StructuredOutput(task="soap", payload={})
        with self.assertRaises(AttributeError):
            vo.task = "other"


class TranscriptionSessionInfoSmokeTest(unittest.TestCase):
    def test_creation(self):
        vo = TranscriptionSessionInfo(
            session_id="s1", state="active", provider_name="aws"
        )
        self.assertEqual(vo.session_id, "s1")

    def test_optional_metadata(self):
        vo = TranscriptionSessionInfo(
            session_id="s1",
            state="active",
            provider_name="aws",
            metadata={"key": "val"},
        )
        self.assertEqual(vo.metadata, {"key": "val"})


class FinalTranscriptSmokeTest(unittest.TestCase):
    def test_creation(self):
        seg = SpeakerSegment(
            speaker="doctor",
            text="hello",
            start_time=0.0,
            end_time=1.0,
            confidence=0.99,
        )
        vo = FinalTranscript(
            session_id="s1",
            text="hello",
            speaker_segments=[seg],
            language="pt-BR",
            provider_name="aws",
        )
        self.assertEqual(vo.text, "hello")
        self.assertEqual(len(vo.speaker_segments), 1)


class FeatureFlagSmokeTest(unittest.TestCase):
    def test_creation(self):
        ff = FeatureFlag(name="beta", enabled=True)
        self.assertEqual(ff.name, "beta")
        self.assertTrue(ff.enabled)
        self.assertEqual(ff.metadata, "")


class ExportResultSmokeTest(unittest.TestCase):
    def test_creation(self):
        er = ExportResult(
            consultation_id="c1",
            format=ExportFormat.PDF,
            data=b"pdf-bytes",
            filename="report.pdf",
        )
        self.assertEqual(er.format, ExportFormat.PDF)
        self.assertEqual(er.data, b"pdf-bytes")


if __name__ == "__main__":
    unittest.main()
