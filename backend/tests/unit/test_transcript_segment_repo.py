"""Unit tests for TranscriptSegmentRepository port and DynamoDB adapter."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.transcription.value_objects import CommittedSegment


def _make_segment(**overrides):
    defaults = dict(
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
    defaults.update(overrides)
    return CommittedSegment(**defaults)


class TranscriptSegmentRepositoryPortTest(unittest.TestCase):
    """Verify port interface defines the expected methods."""

    def test_port_has_save_method(self):
        from deskai.ports.transcript_segment_repository import TranscriptSegmentRepository

        self.assertTrue(hasattr(TranscriptSegmentRepository, "save"))

    def test_port_has_find_by_consultation_method(self):
        from deskai.ports.transcript_segment_repository import TranscriptSegmentRepository

        self.assertTrue(hasattr(TranscriptSegmentRepository, "find_by_consultation"))

    def test_port_has_save_batch_method(self):
        from deskai.ports.transcript_segment_repository import TranscriptSegmentRepository

        self.assertTrue(hasattr(TranscriptSegmentRepository, "save_batch"))


class DynamoDBTranscriptSegmentRepositoryTest(unittest.TestCase):
    """DynamoDB adapter tests for transcript segments."""

    @patch("deskai.adapters.persistence.base_repository.boto3")
    def setUp(self, mock_boto3):
        self.mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = self.mock_table

        from deskai.adapters.persistence.dynamodb_transcript_segment_repository import (
            DynamoDBTranscriptSegmentRepository,
        )

        self.repo = DynamoDBTranscriptSegmentRepository(table_name="test-table")

    def test_save_single_segment(self):
        self.mock_table.put_item.return_value = {}
        segment = _make_segment()

        self.repo.save(segment)

        self.mock_table.put_item.assert_called_once()
        item = self.mock_table.put_item.call_args[1]["Item"]
        self.assertEqual(item["PK"], "CONSULTATION#cons-001")
        self.assertTrue(item["SK"].startswith("SEGMENT#"))
        self.assertEqual(item["speaker"], "doctor")

    def test_save_batch_segments(self):
        self.mock_table.put_item.return_value = {}
        segments = [_make_segment(segment_index=i) for i in range(3)]

        self.repo.save_batch(segments)

        self.assertEqual(self.mock_table.put_item.call_count, 3)

    def test_find_by_consultation_returns_segments(self):
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "PK": "CONSULTATION#cons-001",
                    "SK": "SEGMENT#2026-04-02T10:00:00+00:00#000000",
                    "consultation_id": "cons-001",
                    "session_id": "sess-001",
                    "speaker": "doctor",
                    "text": "Como voce esta?",
                    "start_time": "0.0",
                    "end_time": "1.5",
                    "confidence": "0.95",
                    "is_final": True,
                    "received_at": "2026-04-02T10:00:00+00:00",
                    "segment_index": 0,
                }
            ]
        }

        segments = self.repo.find_by_consultation("cons-001")

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].consultation_id, "cons-001")
        self.assertEqual(segments[0].speaker, "doctor")

    def test_find_by_consultation_empty(self):
        self.mock_table.query.return_value = {"Items": []}

        segments = self.repo.find_by_consultation("cons-missing")

        self.assertEqual(segments, [])

    def test_sk_format_includes_timestamp_and_index(self):
        self.mock_table.put_item.return_value = {}
        segment = _make_segment(
            received_at="2026-04-02T10:05:30+00:00",
            segment_index=42,
        )

        self.repo.save(segment)

        item = self.mock_table.put_item.call_args[1]["Item"]
        self.assertIn("2026-04-02T10:05:30+00:00", item["SK"])
        self.assertIn("000042", item["SK"])


if __name__ == "__main__":
    unittest.main()
