"""WebSocket transcript.commit handler — persist committed transcript segments."""

import json
from uuid import uuid4

from deskai.domain.session.entities import SessionState
from deskai.domain.transcription.value_objects import CommittedSegment
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()


def _normalize_text(value: str) -> str:
    return value.lower().strip()


def _existing_text(segments: list[CommittedSegment]) -> str:
    return " ".join(segment.text for segment in segments if segment.text).lower()


def _build_provisional_events(
    committed_segments: list[CommittedSegment],
    prior_segments: list[CommittedSegment],
) -> list[dict]:
    existing_text = _existing_text(prior_segments)
    events: list[dict] = []

    for segment in committed_segments:
        normalized_text = _normalize_text(segment.text)
        evidence_excerpt = segment.text.strip()
        if not evidence_excerpt:
            continue

        if (
            ("dor" in normalized_text or "queixa" in normalized_text)
            and "dor" not in existing_text
        ):
            events.append(
                {
                    "event": "autofill.candidate",
                    "event_version": "2",
                    "data": {
                        "field_key": "queixa_principal",
                        "candidate_value": evidence_excerpt,
                        "evidence_excerpt": evidence_excerpt,
                        "confidence": segment.confidence,
                    },
                }
            )

            if "alergia" not in existing_text and "alergia" not in normalized_text:
                events.append(
                    {
                        "event": "insight.provisional",
                        "event_version": "2",
                        "data": {
                            "insight_id": str(uuid4()),
                            "category": "documentation_gap",
                            "text": "Alergias ainda nao apareceram no registro parcial.",
                            "severity": "informative",
                            "evidence_excerpt": evidence_excerpt,
                            "is_draft": True,
                        },
                    }
                )

        if (
            ("tomo" in normalized_text or "uso" in normalized_text or "medicamento" in normalized_text)
            and "medicamento" not in existing_text
        ):
            events.append(
                {
                    "event": "autofill.candidate",
                    "event_version": "2",
                    "data": {
                        "field_key": "medicamentos_em_uso",
                        "candidate_value": evidence_excerpt,
                        "evidence_excerpt": evidence_excerpt,
                        "confidence": segment.confidence,
                    },
                }
            )

        if "alerg" in normalized_text and "alerg" not in existing_text:
            events.append(
                {
                    "event": "autofill.candidate",
                    "event_version": "2",
                    "data": {
                        "field_key": "alergias",
                        "candidate_value": evidence_excerpt,
                        "evidence_excerpt": evidence_excerpt,
                        "confidence": segment.confidence,
                    },
                }
            )

        if (
            ("ha " in normalized_text or "dias" in normalized_text or "seman" in normalized_text)
            and "historia_doenca_atual" not in existing_text
        ):
            events.append(
                {
                    "event": "autofill.candidate",
                    "event_version": "2",
                    "data": {
                        "field_key": "historia_doenca_atual",
                        "candidate_value": evidence_excerpt,
                        "evidence_excerpt": evidence_excerpt,
                        "confidence": segment.confidence,
                    },
                }
            )

    return events


def handle_transcript_commit(
    event: dict,
    connection_repo,
    session_repo,
    segment_repo,
    apigw,
) -> dict:
    """Validate connection and session, then persist committed segments."""
    connection_id = event["requestContext"]["connectionId"]
    body = json.loads(event.get("body", "{}"))
    data = body.get("data", {})
    consultation_id = data.get("consultation_id", "")

    logger.info(
        "ws_transcript_commit_requested",
        extra=log_context(
            connection_id=connection_id,
            consultation_id=consultation_id,
        ),
    )

    connection = connection_repo.find_by_connection_id(connection_id)
    if connection is None:
        logger.warning(
            "ws_transcript_commit_unknown_connection",
            extra=log_context(connection_id=connection_id),
        )
        return {"statusCode": 400, "body": "Unknown connection"}

    session = session_repo.find_by_id(connection.session_id)
    if session is None or session.state != SessionState.RECORDING:
        logger.warning(
            "ws_transcript_commit_rejected",
            extra=log_context(
                connection_id=connection_id,
                consultation_id=consultation_id,
                reason="not_recording",
            ),
        )
        return {"statusCode": 400, "body": "Session not recording"}

    raw_segments = data.get("segments", [])
    now = utc_now_iso()

    committed = [
        CommittedSegment(
            consultation_id=consultation_id,
            session_id=session.session_id,
            speaker=seg["speaker"],
            text=seg["text"],
            start_time=seg["start_time"],
            end_time=seg["end_time"],
            confidence=seg["confidence"],
            is_final=seg.get("is_final", False),
            received_at=now,
            segment_index=idx,
        )
        for idx, seg in enumerate(raw_segments)
    ]

    segment_repo.save_batch(committed)
    prior_segments = segment_repo.find_by_consultation(consultation_id)
    prior_length = max(len(prior_segments) - len(committed), 0)
    existing_segments = prior_segments[:prior_length]

    logger.info(
        "ws_transcript_commit_accepted",
        extra=log_context(
            consultation_id=consultation_id,
            segment_count=len(committed),
        ),
    )

    for provisional_event in _build_provisional_events(committed, existing_segments):
        apigw.send_to_connection(
            connection_id=connection_id,
            data=provisional_event,
        )
    return {"statusCode": 200}
