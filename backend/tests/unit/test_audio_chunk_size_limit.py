"""Tests for audio chunk size limit in handle_audio_chunk."""

import base64
import json
from unittest.mock import MagicMock

from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.value_objects import ConnectionInfo
from deskai.handlers.websocket.audio_chunk_handler import (
    MAX_AUDIO_CHUNK_BYTES,
    handle_audio_chunk,
)


def _make_event(audio_bytes: bytes) -> dict:
    audio_b64 = base64.b64encode(audio_bytes).decode()
    return {
        "requestContext": {"connectionId": "conn-1"},
        "body": json.dumps({"action": "audio.chunk", "data": {"audio": audio_b64}}),
    }


def _make_mocks():
    connection = ConnectionInfo(
        connection_id="conn-1",
        session_id="sess-1",
        doctor_id="doc-1",
        clinic_id="clinic-1",
        connected_at="2026-04-02T10:00:00+00:00",
    )

    session = Session(
        session_id="sess-1",
        consultation_id="cons-1",
        doctor_id="doc-1",
        clinic_id="clinic-1",
        state=SessionState.RECORDING,
        started_at="2026-04-02T10:00:00+00:00",
        audio_chunks_received=0,
    )

    conn_repo = MagicMock()
    conn_repo.find_by_connection_id.return_value = connection

    sess_repo = MagicMock()
    sess_repo.find_by_id.return_value = session

    apigw = MagicMock()
    return conn_repo, sess_repo, apigw


class TestAudioChunkSizeLimit:
    def test_chunk_within_limit(self):
        audio = bytes(MAX_AUDIO_CHUNK_BYTES)
        event = _make_event(audio)
        conn_repo, sess_repo, apigw = _make_mocks()
        result = handle_audio_chunk(event, conn_repo, sess_repo, apigw)
        assert result["statusCode"] == 200

    def test_chunk_over_limit(self):
        audio = bytes(MAX_AUDIO_CHUNK_BYTES + 1)
        event = _make_event(audio)
        conn_repo, sess_repo, apigw = _make_mocks()
        result = handle_audio_chunk(event, conn_repo, sess_repo, apigw)
        assert result["statusCode"] == 413
        assert "too large" in result["body"]

    def test_chunk_way_over_limit(self):
        audio = bytes(2 * MAX_AUDIO_CHUNK_BYTES)
        event = _make_event(audio)
        conn_repo, sess_repo, apigw = _make_mocks()
        result = handle_audio_chunk(event, conn_repo, sess_repo, apigw)
        assert result["statusCode"] == 413

    def test_small_chunk_passes(self):
        audio = bytes(100)
        event = _make_event(audio)
        conn_repo, sess_repo, apigw = _make_mocks()
        result = handle_audio_chunk(event, conn_repo, sess_repo, apigw)
        assert result["statusCode"] == 200

    def test_empty_audio_passes(self):
        event = {
            "requestContext": {"connectionId": "conn-1"},
            "body": json.dumps({"action": "audio.chunk", "data": {"audio": ""}}),
        }
        conn_repo, sess_repo, apigw = _make_mocks()
        result = handle_audio_chunk(event, conn_repo, sess_repo, apigw)
        assert result["statusCode"] == 200
