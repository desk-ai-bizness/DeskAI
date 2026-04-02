"""Unit tests for transcription domain entities."""

import unittest

from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.value_objects import (
    CompletenessStatus,
    SpeakerSegment,
)


class NormalizedTranscriptCreationTest(unittest.TestCase):
    def test_create_with_all_fields(self) -> None:
        segments = [
            SpeakerSegment(
                speaker="doctor",
                text="Como voce esta?",
                start_time=0.0,
                end_time=1.5,
                confidence=0.95,
            ),
            SpeakerSegment(
                speaker="patient",
                text="Bem, obrigado.",
                start_time=2.0,
                end_time=3.0,
                confidence=0.90,
            ),
        ]
        t = NormalizedTranscript(
            consultation_id="cons-001",
            provider_name="elevenlabs",
            provider_session_id="el-sess-abc",
            language="pt-BR",
            transcript_text="Como voce esta? Bem, obrigado.",
            speaker_segments=segments,
            timestamps={"start": "2026-04-02T10:00:00+00:00"},
            confidence_metadata={"average": 0.925},
            completeness_status=CompletenessStatus.COMPLETE,
            raw_response_key="s3://bucket/raw/cons-001.json",
            normalized_artifact_key="s3://bucket/normalized/cons-001.json",
            created_at="2026-04-02T10:05:00+00:00",
            updated_at="2026-04-02T10:05:00+00:00",
        )
        self.assertEqual(t.consultation_id, "cons-001")
        self.assertEqual(t.provider_name, "elevenlabs")
        self.assertEqual(t.provider_session_id, "el-sess-abc")
        self.assertEqual(t.language, "pt-BR")
        self.assertEqual(
            t.transcript_text, "Como voce esta? Bem, obrigado."
        )
        self.assertEqual(len(t.speaker_segments), 2)
        self.assertEqual(t.timestamps, {"start": "2026-04-02T10:00:00+00:00"})
        self.assertEqual(t.confidence_metadata, {"average": 0.925})
        self.assertEqual(
            t.completeness_status, CompletenessStatus.COMPLETE
        )
        self.assertEqual(
            t.raw_response_key, "s3://bucket/raw/cons-001.json"
        )
        self.assertEqual(
            t.normalized_artifact_key,
            "s3://bucket/normalized/cons-001.json",
        )
        self.assertEqual(t.created_at, "2026-04-02T10:05:00+00:00")
        self.assertEqual(t.updated_at, "2026-04-02T10:05:00+00:00")

    def test_create_with_defaults(self) -> None:
        t = NormalizedTranscript(
            consultation_id="cons-002",
            provider_name="elevenlabs",
            provider_session_id="el-sess-xyz",
            language="pt-BR",
            transcript_text="",
            speaker_segments=[],
        )
        self.assertEqual(t.consultation_id, "cons-002")
        self.assertEqual(t.transcript_text, "")
        self.assertEqual(t.speaker_segments, [])
        self.assertIsNone(t.timestamps)
        self.assertIsNone(t.confidence_metadata)
        self.assertEqual(
            t.completeness_status, CompletenessStatus.PENDING
        )
        self.assertIsNone(t.raw_response_key)
        self.assertIsNone(t.normalized_artifact_key)
        self.assertEqual(t.created_at, "")
        self.assertEqual(t.updated_at, "")

    def test_entity_is_mutable(self) -> None:
        t = NormalizedTranscript(
            consultation_id="cons-003",
            provider_name="elevenlabs",
            provider_session_id="el-sess-mut",
            language="pt-BR",
            transcript_text="Original text",
            speaker_segments=[],
        )
        t.completeness_status = CompletenessStatus.COMPLETE
        self.assertEqual(
            t.completeness_status, CompletenessStatus.COMPLETE
        )
        t.transcript_text = "Updated text"
        self.assertEqual(t.transcript_text, "Updated text")

    def test_speaker_segments_type(self) -> None:
        seg = SpeakerSegment(
            speaker="doctor",
            text="Ola",
            start_time=0.0,
            end_time=0.5,
            confidence=0.99,
        )
        t = NormalizedTranscript(
            consultation_id="cons-004",
            provider_name="elevenlabs",
            provider_session_id="el-sess-seg",
            language="pt-BR",
            transcript_text="Ola",
            speaker_segments=[seg],
        )
        self.assertIsInstance(t.speaker_segments[0], SpeakerSegment)
        self.assertEqual(t.speaker_segments[0].speaker, "doctor")


if __name__ == "__main__":
    unittest.main()
