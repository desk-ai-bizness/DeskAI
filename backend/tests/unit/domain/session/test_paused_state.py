"""Unit tests for PAUSED session state transitions and validation."""

import unittest

from deskai.domain.session.entities import (
    VALID_SESSION_TRANSITIONS,
    Session,
    SessionState,
)
from deskai.domain.session.exceptions import (
    InvalidSessionStateError,
    SessionPauseRejectedError,
)
from deskai.domain.session.services import SessionService


class SessionStatePausedEnumTest(unittest.TestCase):
    """PAUSED must exist in SessionState and have the correct string value."""

    def test_paused_state_exists(self):
        self.assertEqual(SessionState.PAUSED, "paused")

    def test_paused_is_valid_session_state(self):
        self.assertIn(SessionState.PAUSED, SessionState)


class PausedTransitionsTest(unittest.TestCase):
    """PAUSED state transition rules."""

    def test_recording_to_paused_allowed(self):
        allowed = VALID_SESSION_TRANSITIONS[SessionState.RECORDING]
        self.assertIn(SessionState.PAUSED, allowed)

    def test_paused_to_recording_allowed(self):
        allowed = VALID_SESSION_TRANSITIONS[SessionState.PAUSED]
        self.assertIn(SessionState.RECORDING, allowed)

    def test_paused_to_stopping_allowed(self):
        allowed = VALID_SESSION_TRANSITIONS[SessionState.PAUSED]
        self.assertIn(SessionState.STOPPING, allowed)

    def test_paused_to_disconnected_allowed(self):
        allowed = VALID_SESSION_TRANSITIONS[SessionState.PAUSED]
        self.assertIn(SessionState.DISCONNECTED, allowed)

    def test_active_to_paused_not_allowed(self):
        allowed = VALID_SESSION_TRANSITIONS[SessionState.ACTIVE]
        self.assertNotIn(SessionState.PAUSED, allowed)

    def test_ended_to_paused_not_allowed(self):
        allowed = VALID_SESSION_TRANSITIONS[SessionState.ENDED]
        self.assertNotIn(SessionState.PAUSED, allowed)


class ValidatePauseTest(unittest.TestCase):
    """SessionService.validate_pause must accept RECORDING and reject others."""

    def test_validate_pause_from_recording(self):
        SessionService.validate_pause(SessionState.RECORDING)

    def test_validate_pause_from_paused_raises(self):
        with self.assertRaises(SessionPauseRejectedError):
            SessionService.validate_pause(SessionState.PAUSED)

    def test_validate_pause_from_active_raises(self):
        with self.assertRaises(SessionPauseRejectedError):
            SessionService.validate_pause(SessionState.ACTIVE)

    def test_validate_pause_from_ended_raises(self):
        with self.assertRaises(SessionPauseRejectedError):
            SessionService.validate_pause(SessionState.ENDED)


class ValidateResumeTest(unittest.TestCase):
    """SessionService.validate_resume must accept PAUSED and reject others."""

    def test_validate_resume_from_paused(self):
        SessionService.validate_resume(SessionState.PAUSED)

    def test_validate_resume_from_recording_raises(self):
        with self.assertRaises(SessionPauseRejectedError):
            SessionService.validate_resume(SessionState.RECORDING)

    def test_validate_resume_from_ended_raises(self):
        with self.assertRaises(SessionPauseRejectedError):
            SessionService.validate_resume(SessionState.ENDED)


class ValidateTransitionPausedTest(unittest.TestCase):
    """validate_transition must work correctly with PAUSED state."""

    def test_transition_recording_to_paused(self):
        SessionService.validate_transition(SessionState.RECORDING, SessionState.PAUSED)

    def test_transition_paused_to_recording(self):
        SessionService.validate_transition(SessionState.PAUSED, SessionState.RECORDING)

    def test_transition_paused_to_stopping(self):
        SessionService.validate_transition(SessionState.PAUSED, SessionState.STOPPING)

    def test_transition_active_to_paused_invalid(self):
        with self.assertRaises(InvalidSessionStateError):
            SessionService.validate_transition(SessionState.ACTIVE, SessionState.PAUSED)


class ValidateSessionEndIncludesPausedTest(unittest.TestCase):
    """validate_session_end must accept PAUSED state."""

    def test_session_end_from_paused(self):
        SessionService.validate_session_end(SessionState.PAUSED)


class SessionEntityPausedStateTest(unittest.TestCase):
    """Session entity must accept PAUSED state."""

    def test_create_session_with_paused_state(self):
        session = Session(
            session_id="sess-001",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.PAUSED,
            started_at="2026-04-02T10:00:00+00:00",
        )
        self.assertEqual(session.state, SessionState.PAUSED)


if __name__ == "__main__":
    unittest.main()
