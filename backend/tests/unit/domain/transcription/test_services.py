"""Unit tests for TranscriptionNormalizer domain service."""

import unittest

from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.exceptions import NormalizationError
from deskai.domain.transcription.services import TranscriptionNormalizer
from deskai.domain.transcription.value_objects import (
    CompletenessStatus,
    PartialTranscript,
    SpeakerSegment,
)


def _make_elevenlabs_response(**overrides: object) -> dict:
    """Build a minimal ElevenLabs Scribe v2 response with sensible defaults."""
    base: dict = {
        "language_code": "pt",
        "text": "Doutor, eu sinto dor de cabeca. Ha quanto tempo?",
        "words": [
            {
                "text": "Doutor,",
                "start": 0.0,
                "end": 0.5,
                "type": "word",
                "speaker_id": "speaker_1",
            },
            {
                "text": "eu",
                "start": 0.5,
                "end": 0.7,
                "type": "word",
                "speaker_id": "speaker_1",
            },
            {
                "text": "sinto",
                "start": 0.7,
                "end": 1.0,
                "type": "word",
                "speaker_id": "speaker_1",
            },
            {
                "text": "dor",
                "start": 1.0,
                "end": 1.2,
                "type": "word",
                "speaker_id": "speaker_1",
            },
            {
                "text": "de",
                "start": 1.2,
                "end": 1.3,
                "type": "word",
                "speaker_id": "speaker_1",
            },
            {
                "text": "cabeca.",
                "start": 1.3,
                "end": 1.8,
                "type": "word",
                "speaker_id": "speaker_1",
            },
            {
                "text": "Ha",
                "start": 2.0,
                "end": 2.2,
                "type": "word",
                "speaker_id": "speaker_0",
            },
            {
                "text": "quanto",
                "start": 2.2,
                "end": 2.5,
                "type": "word",
                "speaker_id": "speaker_0",
            },
            {
                "text": "tempo?",
                "start": 2.5,
                "end": 2.9,
                "type": "word",
                "speaker_id": "speaker_0",
            },
        ],
    }
    base.update(overrides)
    return base


class NormalizeElevenLabsResponseTest(unittest.TestCase):
    def test_normalize_basic_response(self) -> None:
        raw = _make_elevenlabs_response()
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        self.assertIsInstance(result, NormalizedTranscript)
        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.provider_name, "elevenlabs")
        self.assertEqual(result.provider_session_id, "el-sess-001")
        self.assertEqual(result.language, "pt-BR")
        self.assertEqual(
            result.transcript_text,
            "Doutor, eu sinto dor de cabeca. Ha quanto tempo?",
        )

    def test_normalize_produces_speaker_segments(self) -> None:
        raw = _make_elevenlabs_response()
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        self.assertGreater(len(result.speaker_segments), 0)
        for seg in result.speaker_segments:
            self.assertIsInstance(seg, SpeakerSegment)
            self.assertIn(
                seg.speaker, ("speaker_0", "speaker_1")
            )
            self.assertIsInstance(seg.start_time, float)
            self.assertIsInstance(seg.end_time, float)

    def test_normalize_groups_consecutive_same_speaker(self) -> None:
        raw = _make_elevenlabs_response()
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        # speaker_1 words then speaker_0 words => 2 segments
        self.assertEqual(len(result.speaker_segments), 2)
        self.assertEqual(result.speaker_segments[0].speaker, "speaker_1")
        self.assertEqual(result.speaker_segments[1].speaker, "speaker_0")

    def test_normalize_sets_completeness_complete(self) -> None:
        raw = _make_elevenlabs_response()
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        self.assertEqual(
            result.completeness_status, CompletenessStatus.COMPLETE
        )

    def test_normalize_empty_text_sets_failed(self) -> None:
        raw = _make_elevenlabs_response(text="", words=[])
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        self.assertEqual(
            result.completeness_status, CompletenessStatus.FAILED
        )

    def test_normalize_missing_words_key(self) -> None:
        raw = {"language_code": "pt", "text": "Ola"}
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        self.assertEqual(result.transcript_text, "Ola")
        self.assertEqual(result.speaker_segments, [])
        self.assertEqual(
            result.completeness_status, CompletenessStatus.PARTIAL
        )

    def test_normalize_missing_speaker_id_in_words(self) -> None:
        raw = {
            "language_code": "pt",
            "text": "Oi tudo bem",
            "words": [
                {"text": "Oi", "start": 0.0, "end": 0.3, "type": "word"},
                {
                    "text": "tudo",
                    "start": 0.3,
                    "end": 0.6,
                    "type": "word",
                },
                {
                    "text": "bem",
                    "start": 0.6,
                    "end": 0.9,
                    "type": "word",
                },
            ],
        }
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        # Words without speaker_id should get "unknown"
        for seg in result.speaker_segments:
            self.assertEqual(seg.speaker, "unknown")

    def test_normalize_raises_on_missing_text_key(self) -> None:
        raw = {"language_code": "pt", "words": []}
        with self.assertRaises(NormalizationError):
            TranscriptionNormalizer.normalize_elevenlabs_response(
                raw_response=raw,
                consultation_id="cons-001",
                provider_session_id="el-sess-001",
            )

    def test_normalize_confidence_metadata(self) -> None:
        raw = _make_elevenlabs_response()
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        self.assertIsNotNone(result.confidence_metadata)
        self.assertIn("word_count", result.confidence_metadata)
        self.assertIn("segment_count", result.confidence_metadata)

    def test_normalize_timestamps_metadata(self) -> None:
        raw = _make_elevenlabs_response()
        result = TranscriptionNormalizer.normalize_elevenlabs_response(
            raw_response=raw,
            consultation_id="cons-001",
            provider_session_id="el-sess-001",
        )
        self.assertIsNotNone(result.timestamps)


class ValidateTranscriptCompletenessTest(unittest.TestCase):
    def test_complete_transcript(self) -> None:
        seg = SpeakerSegment(
            speaker="doctor",
            text="Ola",
            start_time=0.0,
            end_time=0.5,
            confidence=0.95,
        )
        t = NormalizedTranscript(
            consultation_id="cons-001",
            provider_name="elevenlabs",
            provider_session_id="el-sess-001",
            language="pt-BR",
            transcript_text="Ola",
            speaker_segments=[seg],
            completeness_status=CompletenessStatus.COMPLETE,
        )
        result = TranscriptionNormalizer.validate_transcript_completeness(t)
        self.assertEqual(result, CompletenessStatus.COMPLETE)

    def test_empty_text_is_failed(self) -> None:
        t = NormalizedTranscript(
            consultation_id="cons-002",
            provider_name="elevenlabs",
            provider_session_id="el-sess-002",
            language="pt-BR",
            transcript_text="",
            speaker_segments=[],
        )
        result = TranscriptionNormalizer.validate_transcript_completeness(t)
        self.assertEqual(result, CompletenessStatus.FAILED)

    def test_text_without_segments_is_partial(self) -> None:
        t = NormalizedTranscript(
            consultation_id="cons-003",
            provider_name="elevenlabs",
            provider_session_id="el-sess-003",
            language="pt-BR",
            transcript_text="Some text here",
            speaker_segments=[],
        )
        result = TranscriptionNormalizer.validate_transcript_completeness(t)
        self.assertEqual(result, CompletenessStatus.PARTIAL)


class NormalizePartialResponseTest(unittest.TestCase):
    def test_normalize_partial_response(self) -> None:
        raw_partial = {
            "text": "Doutor eu sinto",
            "speaker_id": "speaker_0",
            "is_final": False,
            "timestamp": "2026-04-02T10:01:00+00:00",
        }
        result = TranscriptionNormalizer.normalize_partial_response(
            raw_partial
        )
        self.assertIsInstance(result, PartialTranscript)
        self.assertEqual(result.text, "Doutor eu sinto")
        self.assertEqual(result.speaker, "speaker_0")
        self.assertFalse(result.is_final)
        self.assertEqual(result.timestamp, "2026-04-02T10:01:00+00:00")

    def test_normalize_partial_final(self) -> None:
        raw_partial = {
            "text": "Dor de cabeca ha dois dias.",
            "speaker_id": "speaker_1",
            "is_final": True,
            "timestamp": "2026-04-02T10:02:00+00:00",
        }
        result = TranscriptionNormalizer.normalize_partial_response(
            raw_partial
        )
        self.assertTrue(result.is_final)
        self.assertEqual(result.speaker, "speaker_1")

    def test_normalize_partial_missing_speaker(self) -> None:
        raw_partial = {
            "text": "Algo",
            "is_final": False,
            "timestamp": "2026-04-02T10:03:00+00:00",
        }
        result = TranscriptionNormalizer.normalize_partial_response(
            raw_partial
        )
        self.assertEqual(result.speaker, "unknown")

    def test_normalize_partial_missing_text_raises(self) -> None:
        raw_partial = {
            "speaker_id": "speaker_0",
            "is_final": False,
            "timestamp": "2026-04-02T10:04:00+00:00",
        }
        with self.assertRaises(NormalizationError):
            TranscriptionNormalizer.normalize_partial_response(raw_partial)

    def test_normalize_partial_default_confidence(self) -> None:
        raw_partial = {
            "text": "Oi",
            "speaker_id": "speaker_0",
            "is_final": True,
            "timestamp": "2026-04-02T10:05:00+00:00",
        }
        result = TranscriptionNormalizer.normalize_partial_response(
            raw_partial
        )
        self.assertEqual(result.confidence, 0.0)

    def test_normalize_partial_with_confidence(self) -> None:
        raw_partial = {
            "text": "Oi",
            "speaker_id": "speaker_0",
            "is_final": True,
            "timestamp": "2026-04-02T10:05:00+00:00",
            "confidence": 0.87,
        }
        result = TranscriptionNormalizer.normalize_partial_response(
            raw_partial
        )
        self.assertEqual(result.confidence, 0.87)


if __name__ == "__main__":
    unittest.main()
