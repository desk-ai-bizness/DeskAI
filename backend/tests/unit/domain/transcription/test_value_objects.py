"""Unit tests for transcription domain value objects."""

import unittest

from deskai.domain.transcription.value_objects import (
    CompletenessStatus,
    PartialTranscript,
    SpeakerSegment,
    TranscriptionLanguage,
)


class SpeakerSegmentTest(unittest.TestCase):
    def test_create_speaker_segment(self) -> None:
        seg = SpeakerSegment(
            speaker="doctor",
            text="Como voce esta se sentindo?",
            start_time=0.0,
            end_time=2.5,
            confidence=0.95,
        )
        self.assertEqual(seg.speaker, "doctor")
        self.assertEqual(seg.text, "Como voce esta se sentindo?")
        self.assertEqual(seg.start_time, 0.0)
        self.assertEqual(seg.end_time, 2.5)
        self.assertEqual(seg.confidence, 0.95)

    def test_speaker_segment_is_frozen(self) -> None:
        seg = SpeakerSegment(
            speaker="patient",
            text="Estou bem.",
            start_time=3.0,
            end_time=4.0,
            confidence=0.88,
        )
        with self.assertRaises(AttributeError):
            seg.speaker = "doctor"

    def test_speaker_segment_equality(self) -> None:
        a = SpeakerSegment(
            speaker="doctor",
            text="Oi",
            start_time=0.0,
            end_time=1.0,
            confidence=0.9,
        )
        b = SpeakerSegment(
            speaker="doctor",
            text="Oi",
            start_time=0.0,
            end_time=1.0,
            confidence=0.9,
        )
        self.assertEqual(a, b)


class CompletenessStatusTest(unittest.TestCase):
    def test_all_status_values_exist(self) -> None:
        expected = {"complete", "partial", "failed", "pending"}
        actual = {s.value for s in CompletenessStatus}
        self.assertEqual(actual, expected)

    def test_status_count(self) -> None:
        self.assertEqual(len(CompletenessStatus), 4)

    def test_status_from_string(self) -> None:
        self.assertEqual(
            CompletenessStatus("complete"), CompletenessStatus.COMPLETE
        )
        self.assertEqual(
            CompletenessStatus("partial"), CompletenessStatus.PARTIAL
        )
        self.assertEqual(
            CompletenessStatus("failed"), CompletenessStatus.FAILED
        )
        self.assertEqual(
            CompletenessStatus("pending"), CompletenessStatus.PENDING
        )


class TranscriptionLanguageTest(unittest.TestCase):
    def test_pt_br_value(self) -> None:
        self.assertEqual(TranscriptionLanguage.PT_BR.value, "pt-BR")

    def test_language_from_string(self) -> None:
        self.assertEqual(
            TranscriptionLanguage("pt-BR"), TranscriptionLanguage.PT_BR
        )


class PartialTranscriptTest(unittest.TestCase):
    def test_create_partial_transcript(self) -> None:
        p = PartialTranscript(
            text="Doutor, eu tenho sentido dor de cabeca",
            speaker="patient",
            is_final=False,
            timestamp="2026-04-02T10:01:00+00:00",
            confidence=0.82,
        )
        self.assertEqual(
            p.text, "Doutor, eu tenho sentido dor de cabeca"
        )
        self.assertEqual(p.speaker, "patient")
        self.assertFalse(p.is_final)
        self.assertEqual(p.timestamp, "2026-04-02T10:01:00+00:00")
        self.assertEqual(p.confidence, 0.82)

    def test_partial_transcript_is_frozen(self) -> None:
        p = PartialTranscript(
            text="Oi",
            speaker="doctor",
            is_final=True,
            timestamp="2026-04-02T10:00:00+00:00",
            confidence=0.99,
        )
        with self.assertRaises(AttributeError):
            p.text = "Changed"

    def test_partial_transcript_equality(self) -> None:
        a = PartialTranscript(
            text="Oi",
            speaker="doctor",
            is_final=True,
            timestamp="2026-04-02T10:00:00+00:00",
            confidence=0.99,
        )
        b = PartialTranscript(
            text="Oi",
            speaker="doctor",
            is_final=True,
            timestamp="2026-04-02T10:00:00+00:00",
            confidence=0.99,
        )
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
