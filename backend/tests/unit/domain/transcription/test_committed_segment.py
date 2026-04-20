"""Unit tests for CommittedSegment value object."""

import unittest

from deskai.domain.transcription.value_objects import CommittedSegment
from deskai.shared.errors import DomainValidationError


class CommittedSegmentTest(unittest.TestCase):
    """CommittedSegment value object validation tests."""

    def test_valid_segment(self):
        seg = CommittedSegment(
            consultation_id="cons-001",
            session_id="sess-001",
            speaker="doctor",
            text="Como voce esta?",
            start_time=0.0,
            end_time=1.5,
            confidence=0.95,
            is_final=True,
            received_at="2026-04-02T10:00:00+00:00",
            segment_index=0,
        )
        self.assertEqual(seg.speaker, "doctor")
        self.assertEqual(seg.segment_index, 0)

    def test_empty_consultation_id_raises(self):
        with self.assertRaises(DomainValidationError):
            CommittedSegment(
                consultation_id="",
                session_id="sess-001",
                speaker="doctor",
                text="text",
                start_time=0.0,
                end_time=1.0,
                confidence=0.9,
                is_final=True,
                received_at="2026-04-02T10:00:00+00:00",
                segment_index=0,
            )

    def test_negative_segment_index_raises(self):
        with self.assertRaises(DomainValidationError):
            CommittedSegment(
                consultation_id="cons-001",
                session_id="sess-001",
                speaker="doctor",
                text="text",
                start_time=0.0,
                end_time=1.0,
                confidence=0.9,
                is_final=True,
                received_at="2026-04-02T10:00:00+00:00",
                segment_index=-1,
            )

    def test_confidence_out_of_range_raises(self):
        with self.assertRaises(DomainValidationError):
            CommittedSegment(
                consultation_id="cons-001",
                session_id="sess-001",
                speaker="doctor",
                text="text",
                start_time=0.0,
                end_time=1.0,
                confidence=1.5,
                is_final=True,
                received_at="2026-04-02T10:00:00+00:00",
                segment_index=0,
            )

    def test_frozen_immutability(self):
        seg = CommittedSegment(
            consultation_id="cons-001",
            session_id="sess-001",
            speaker="patient",
            text="Estou bem.",
            start_time=0.0,
            end_time=1.0,
            confidence=0.8,
            is_final=True,
            received_at="2026-04-02T10:00:00+00:00",
            segment_index=0,
        )
        with self.assertRaises(AttributeError):
            seg.text = "changed"


if __name__ == "__main__":
    unittest.main()
