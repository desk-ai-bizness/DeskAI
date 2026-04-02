"""Transcription domain services — pure functions for normalization."""

from typing import Any

from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.exceptions import NormalizationError
from deskai.domain.transcription.value_objects import (
    CompletenessStatus,
    PartialTranscript,
    SpeakerSegment,
)
from deskai.shared.time import utc_now_iso

_LANGUAGE_MAP: dict[str, str] = {
    "pt": "pt-BR",
}


class TranscriptionNormalizer:
    """Pure domain service for normalizing transcription provider responses."""

    @staticmethod
    def normalize_elevenlabs_response(
        raw_response: dict[str, Any],
        consultation_id: str,
        provider_session_id: str,
    ) -> NormalizedTranscript:
        """Normalize an ElevenLabs Scribe v2 response into a NormalizedTranscript."""
        if "text" not in raw_response:
            raise NormalizationError(
                "Raw response missing required 'text' field"
            )

        text = raw_response["text"]
        raw_lang = raw_response.get("language_code", "pt")
        language = _LANGUAGE_MAP.get(raw_lang, raw_lang)
        words = raw_response.get("words", [])

        segments = TranscriptionNormalizer._group_words_into_segments(words)
        completeness = TranscriptionNormalizer._determine_completeness(
            text, words, segments
        )

        now = utc_now_iso()
        return NormalizedTranscript(
            consultation_id=consultation_id,
            provider_name="elevenlabs",
            provider_session_id=provider_session_id,
            language=language,
            transcript_text=text,
            speaker_segments=segments,
            timestamps={"normalized_at": now},
            confidence_metadata={
                "word_count": len(words),
                "segment_count": len(segments),
            },
            completeness_status=completeness,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def validate_transcript_completeness(
        transcript: NormalizedTranscript,
    ) -> CompletenessStatus:
        """Validate and return the completeness status of a transcript."""
        if not transcript.transcript_text:
            return CompletenessStatus.FAILED
        if not transcript.speaker_segments:
            return CompletenessStatus.PARTIAL
        return CompletenessStatus.COMPLETE

    @staticmethod
    def normalize_partial_response(
        raw_partial: dict[str, Any],
    ) -> PartialTranscript:
        """Normalize a real-time partial transcription update."""
        if "text" not in raw_partial:
            raise NormalizationError(
                "Partial response missing required 'text' field"
            )

        return PartialTranscript(
            text=raw_partial["text"],
            speaker=raw_partial.get("speaker_id", "unknown"),
            is_final=raw_partial.get("is_final", False),
            timestamp=raw_partial.get("timestamp", ""),
            confidence=raw_partial.get("confidence", 0.0),
        )

    @staticmethod
    def _group_words_into_segments(
        words: list[dict[str, Any]],
    ) -> list[SpeakerSegment]:
        """Group consecutive words by speaker into SpeakerSegments."""
        if not words:
            return []

        segments: list[SpeakerSegment] = []
        current_speaker: str | None = None
        current_words: list[str] = []
        current_start: float = 0.0
        current_end: float = 0.0

        for word in words:
            speaker = word.get("speaker_id", "unknown")
            if speaker != current_speaker:
                if current_speaker is not None and current_words:
                    segments.append(
                        SpeakerSegment(
                            speaker=current_speaker,
                            text=" ".join(current_words),
                            start_time=current_start,
                            end_time=current_end,
                            confidence=0.0,
                        )
                    )
                current_speaker = speaker
                current_words = [word.get("text", "")]
                current_start = float(word.get("start", 0.0))
                current_end = float(word.get("end", 0.0))
            else:
                current_words.append(word.get("text", ""))
                current_end = float(word.get("end", 0.0))

        if current_speaker is not None and current_words:
            segments.append(
                SpeakerSegment(
                    speaker=current_speaker,
                    text=" ".join(current_words),
                    start_time=current_start,
                    end_time=current_end,
                    confidence=0.0,
                )
            )

        return segments

    @staticmethod
    def _determine_completeness(
        text: str,
        words: list[dict[str, Any]],
        segments: list[SpeakerSegment],
    ) -> CompletenessStatus:
        """Determine completeness status from response content."""
        if not text:
            return CompletenessStatus.FAILED
        if not words or not segments:
            return CompletenessStatus.PARTIAL
        return CompletenessStatus.COMPLETE
