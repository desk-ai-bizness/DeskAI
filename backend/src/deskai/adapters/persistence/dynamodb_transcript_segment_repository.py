"""DynamoDB adapter for transcript segment persistence."""

from deskai.adapters.persistence.base_repository import DynamoDBBaseRepository
from deskai.domain.transcription.value_objects import CommittedSegment
from deskai.ports.transcript_segment_repository import TranscriptSegmentRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


class DynamoDBTranscriptSegmentRepository(DynamoDBBaseRepository, TranscriptSegmentRepository):
    """Persist and query committed transcript segments in DynamoDB.

    Key schema:
        PK = CONSULTATION#{consultation_id}
        SK = SEGMENT#{received_at}#{segment_index:06d}
    """

    def save(self, segment: CommittedSegment) -> None:
        self._safe_put_item(Item=self._to_item(segment))
        logger.debug(
            "dynamodb_segment_saved",
            extra=log_context(
                consultation_id=segment.consultation_id,
                segment_index=segment.segment_index,
            ),
        )

    def save_batch(self, segments: list[CommittedSegment]) -> None:
        for segment in segments:
            self.save(segment)

    def find_by_consultation(self, consultation_id: str) -> list[CommittedSegment]:
        response = self._safe_query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"CONSULTATION#{consultation_id}",
                ":sk_prefix": "SEGMENT#",
            },
        )
        items = response.get("Items", [])
        logger.debug(
            "dynamodb_segments_found",
            extra=log_context(
                consultation_id=consultation_id,
                count=len(items),
            ),
        )
        return [self._to_entity(item) for item in items]

    @staticmethod
    def _to_item(segment: CommittedSegment) -> dict:
        sk = f"SEGMENT#{segment.received_at}#{segment.segment_index:06d}"
        return {
            "PK": f"CONSULTATION#{segment.consultation_id}",
            "SK": sk,
            "consultation_id": segment.consultation_id,
            "session_id": segment.session_id,
            "speaker": segment.speaker,
            "text": segment.text,
            "start_time": str(segment.start_time),
            "end_time": str(segment.end_time),
            "confidence": str(segment.confidence),
            "is_final": segment.is_final,
            "received_at": segment.received_at,
            "segment_index": segment.segment_index,
        }

    @staticmethod
    def _to_entity(item: dict) -> CommittedSegment:
        return CommittedSegment(
            consultation_id=item["consultation_id"],
            session_id=item["session_id"],
            speaker=item["speaker"],
            text=item["text"],
            start_time=float(item.get("start_time", 0)),
            end_time=float(item.get("end_time", 0)),
            confidence=float(item.get("confidence", 0)),
            is_final=bool(item.get("is_final", False)),
            received_at=item["received_at"],
            segment_index=int(item.get("segment_index", 0)),
        )
