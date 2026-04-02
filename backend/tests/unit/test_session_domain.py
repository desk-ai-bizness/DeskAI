"""Unit tests for session domain: entities, value objects, services, exceptions."""

import unittest
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import (
    AudioChunkRejectedError,
    GracePeriodExpiredError,
    InvalidSessionStateError,
    SessionAlreadyActiveError,
    SessionNotActiveError,
    SessionNotFoundError,
    SessionOwnershipError,
)
from deskai.domain.session.services import SessionService
from deskai.domain.session.value_objects import AudioChunk, ConnectionInfo
from deskai.shared.errors import DeskAIError

# ---------------------------------------------------------------------------
# SessionState enum
# ---------------------------------------------------------------------------


class TestSessionState(unittest.TestCase):
    def test_all_states_exist(self):
        assert SessionState.CONNECTING == "connecting"
        assert SessionState.ACTIVE == "active"
        assert SessionState.RECORDING == "recording"
        assert SessionState.STOPPING == "stopping"
        assert SessionState.ENDED == "ended"
        assert SessionState.DISCONNECTED == "disconnected"

    def test_state_count(self):
        assert len(SessionState) == 6


# ---------------------------------------------------------------------------
# Session entity
# ---------------------------------------------------------------------------


class TestSession(unittest.TestCase):
    def test_creation_with_defaults(self):
        s = Session(
            session_id="s-1",
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
        )
        assert s.session_id == "s-1"
        assert s.consultation_id == "c-1"
        assert s.doctor_id == "d-1"
        assert s.clinic_id == "cl-1"
        assert s.connection_id is None
        assert s.state == SessionState.CONNECTING
        assert s.started_at == ""
        assert s.ended_at is None
        assert s.duration_seconds == 0
        assert s.audio_chunks_received == 0
        assert s.grace_period_expires_at is None
        assert s.last_activity_at is None

    def test_creation_with_all_fields(self):
        s = Session(
            session_id="s-2",
            consultation_id="c-2",
            doctor_id="d-2",
            clinic_id="cl-2",
            connection_id="conn-1",
            state=SessionState.RECORDING,
            started_at="2026-04-01T10:00:00+00:00",
            ended_at="2026-04-01T10:30:00+00:00",
            duration_seconds=1800,
            audio_chunks_received=42,
            grace_period_expires_at="2026-04-01T10:35:00+00:00",
            last_activity_at="2026-04-01T10:29:00+00:00",
        )
        assert s.state == SessionState.RECORDING
        assert s.duration_seconds == 1800
        assert s.audio_chunks_received == 42

    def test_session_is_mutable_dataclass(self):
        s = Session(
            session_id="s-1",
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
        )
        s.state = SessionState.ACTIVE
        assert s.state == SessionState.ACTIVE


# ---------------------------------------------------------------------------
# AudioChunk value object
# ---------------------------------------------------------------------------


class TestAudioChunk(unittest.TestCase):
    def test_creation(self):
        chunk = AudioChunk(
            chunk_index=0,
            audio_data=b"\x00\x01\x02",
            timestamp="2026-04-01T10:00:01+00:00",
            session_id="s-1",
        )
        assert chunk.chunk_index == 0
        assert chunk.audio_data == b"\x00\x01\x02"
        assert chunk.session_id == "s-1"

    def test_frozen_immutability(self):
        chunk = AudioChunk(
            chunk_index=0,
            audio_data=b"\x00",
            timestamp="2026-04-01T10:00:01+00:00",
            session_id="s-1",
        )
        with self.assertRaises(FrozenInstanceError):
            chunk.chunk_index = 5


# ---------------------------------------------------------------------------
# ConnectionInfo value object
# ---------------------------------------------------------------------------


class TestConnectionInfo(unittest.TestCase):
    def test_creation(self):
        conn = ConnectionInfo(
            connection_id="conn-1",
            session_id="s-1",
            doctor_id="d-1",
            clinic_id="cl-1",
            connected_at="2026-04-01T10:00:00+00:00",
        )
        assert conn.connection_id == "conn-1"
        assert conn.session_id == "s-1"
        assert conn.doctor_id == "d-1"
        assert conn.clinic_id == "cl-1"

    def test_frozen_immutability(self):
        conn = ConnectionInfo(
            connection_id="conn-1",
            session_id="s-1",
            doctor_id="d-1",
            clinic_id="cl-1",
            connected_at="2026-04-01T10:00:00+00:00",
        )
        with self.assertRaises(FrozenInstanceError):
            conn.connection_id = "conn-2"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions(unittest.TestCase):
    def test_all_exceptions_inherit_from_deskai_error(self):
        exceptions = [
            SessionNotFoundError,
            SessionAlreadyActiveError,
            SessionNotActiveError,
            InvalidSessionStateError,
            AudioChunkRejectedError,
            GracePeriodExpiredError,
            SessionOwnershipError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, DeskAIError)

    def test_exceptions_are_instantiable_with_message(self):
        for exc_class in [
            SessionNotFoundError,
            SessionAlreadyActiveError,
            SessionNotActiveError,
            InvalidSessionStateError,
            AudioChunkRejectedError,
            GracePeriodExpiredError,
            SessionOwnershipError,
        ]:
            exc = exc_class("test message")
            assert str(exc) == "test message"


# ---------------------------------------------------------------------------
# SessionService — validate_session_start
# ---------------------------------------------------------------------------


class TestValidateSessionStart(unittest.TestCase):
    def test_success_when_started_and_correct_doctor(self):
        SessionService.validate_session_start(
            consultation_status=ConsultationStatus.STARTED,
            consultation_doctor_id="d-1",
            requesting_doctor_id="d-1",
        )

    def test_raises_when_consultation_not_started_recording(self):
        with self.assertRaises(InvalidSessionStateError):
            SessionService.validate_session_start(
                consultation_status=ConsultationStatus.RECORDING,
                consultation_doctor_id="d-1",
                requesting_doctor_id="d-1",
            )

    def test_raises_when_consultation_finalized(self):
        with self.assertRaises(InvalidSessionStateError):
            SessionService.validate_session_start(
                consultation_status=ConsultationStatus.FINALIZED,
                consultation_doctor_id="d-1",
                requesting_doctor_id="d-1",
            )

    def test_raises_when_consultation_in_processing(self):
        with self.assertRaises(InvalidSessionStateError):
            SessionService.validate_session_start(
                consultation_status=ConsultationStatus.IN_PROCESSING,
                consultation_doctor_id="d-1",
                requesting_doctor_id="d-1",
            )

    def test_raises_when_wrong_doctor(self):
        with self.assertRaises(SessionOwnershipError):
            SessionService.validate_session_start(
                consultation_status=ConsultationStatus.STARTED,
                consultation_doctor_id="d-1",
                requesting_doctor_id="d-999",
            )


# ---------------------------------------------------------------------------
# SessionService — validate_audio_chunk
# ---------------------------------------------------------------------------


class TestValidateAudioChunk(unittest.TestCase):
    def test_success_when_recording_and_correct_doctor(self):
        SessionService.validate_audio_chunk(
            session_state=SessionState.RECORDING,
            session_doctor_id="d-1",
            requesting_doctor_id="d-1",
        )

    def test_success_when_active_and_correct_doctor(self):
        SessionService.validate_audio_chunk(
            session_state=SessionState.ACTIVE,
            session_doctor_id="d-1",
            requesting_doctor_id="d-1",
        )

    def test_raises_when_ended(self):
        with self.assertRaises(AudioChunkRejectedError):
            SessionService.validate_audio_chunk(
                session_state=SessionState.ENDED,
                session_doctor_id="d-1",
                requesting_doctor_id="d-1",
            )

    def test_raises_when_stopping(self):
        with self.assertRaises(AudioChunkRejectedError):
            SessionService.validate_audio_chunk(
                session_state=SessionState.STOPPING,
                session_doctor_id="d-1",
                requesting_doctor_id="d-1",
            )

    def test_raises_when_wrong_doctor(self):
        with self.assertRaises(SessionOwnershipError):
            SessionService.validate_audio_chunk(
                session_state=SessionState.RECORDING,
                session_doctor_id="d-1",
                requesting_doctor_id="d-999",
            )


# ---------------------------------------------------------------------------
# SessionService — validate_session_end
# ---------------------------------------------------------------------------


class TestValidateSessionEnd(unittest.TestCase):
    def test_success_when_recording(self):
        SessionService.validate_session_end(session_state=SessionState.RECORDING)

    def test_success_when_active(self):
        SessionService.validate_session_end(session_state=SessionState.ACTIVE)

    def test_raises_when_ended(self):
        with self.assertRaises(InvalidSessionStateError):
            SessionService.validate_session_end(session_state=SessionState.ENDED)

    def test_raises_when_connecting(self):
        with self.assertRaises(InvalidSessionStateError):
            SessionService.validate_session_end(session_state=SessionState.CONNECTING)


# ---------------------------------------------------------------------------
# SessionService — compute_grace_period_expiry
# ---------------------------------------------------------------------------


class TestComputeGracePeriodExpiry(unittest.TestCase):
    def test_default_five_minutes(self):
        disconnect_time = "2026-04-01T10:00:00+00:00"
        result = SessionService.compute_grace_period_expiry(disconnect_time)
        expected = datetime(2026, 4, 1, 10, 5, 0, tzinfo=UTC).isoformat()
        assert result == expected

    def test_custom_grace_minutes(self):
        disconnect_time = "2026-04-01T10:00:00+00:00"
        result = SessionService.compute_grace_period_expiry(
            disconnect_time, grace_minutes=10
        )
        expected = datetime(2026, 4, 1, 10, 10, 0, tzinfo=UTC).isoformat()
        assert result == expected


# ---------------------------------------------------------------------------
# SessionService — is_grace_period_expired
# ---------------------------------------------------------------------------


class TestIsGracePeriodExpired(unittest.TestCase):
    def test_expired_when_current_time_past_expiry(self):
        expiry = "2026-04-01T10:05:00+00:00"
        current = "2026-04-01T10:06:00+00:00"
        assert SessionService.is_grace_period_expired(expiry, current) is True

    def test_not_expired_when_current_time_before_expiry(self):
        expiry = "2026-04-01T10:05:00+00:00"
        current = "2026-04-01T10:03:00+00:00"
        assert SessionService.is_grace_period_expired(expiry, current) is False

    def test_expired_when_exactly_at_expiry(self):
        expiry = "2026-04-01T10:05:00+00:00"
        current = "2026-04-01T10:05:00+00:00"
        assert SessionService.is_grace_period_expired(expiry, current) is True


# ---------------------------------------------------------------------------
# SessionService — can_reconnect
# ---------------------------------------------------------------------------


class TestCanReconnect(unittest.TestCase):
    def test_true_when_disconnected_and_grace_not_expired(self):
        s = Session(
            session_id="s-1",
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
            state=SessionState.DISCONNECTED,
            grace_period_expires_at="2099-12-31T23:59:59+00:00",
        )
        assert SessionService.can_reconnect(s) is True

    def test_false_when_disconnected_and_grace_expired(self):
        s = Session(
            session_id="s-1",
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
            state=SessionState.DISCONNECTED,
            grace_period_expires_at="2020-01-01T00:00:00+00:00",
        )
        assert SessionService.can_reconnect(s) is False

    def test_false_when_ended(self):
        s = Session(
            session_id="s-1",
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
            state=SessionState.ENDED,
        )
        assert SessionService.can_reconnect(s) is False

    def test_false_when_active(self):
        s = Session(
            session_id="s-1",
            consultation_id="c-1",
            doctor_id="d-1",
            clinic_id="cl-1",
            state=SessionState.ACTIVE,
        )
        assert SessionService.can_reconnect(s) is False
