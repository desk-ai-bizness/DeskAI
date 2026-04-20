"""Unit tests for PauseSessionUseCase and ResumeSessionUseCase."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import (
    SessionNotFoundError,
    SessionOwnershipError,
    SessionPauseRejectedError,
)


def _make_session(state=SessionState.RECORDING, **overrides):
    defaults = dict(
        session_id="sess-001",
        consultation_id="cons-001",
        doctor_id="doc-001",
        clinic_id="clinic-001",
        state=state,
        started_at="2026-04-02T10:00:00+00:00",
    )
    defaults.update(overrides)
    return Session(**defaults)


class PauseSessionUseCaseTest(unittest.TestCase):
    def setUp(self):
        self.session_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.session.pause_session import PauseSessionUseCase

        self.use_case = PauseSessionUseCase(
            session_repo=self.session_repo,
            audit_repo=self.audit_repo,
        )

    @patch(
        "deskai.application.session.pause_session.new_uuid",
        return_value="evt-001",
    )
    @patch(
        "deskai.application.session.pause_session.utc_now_iso",
        return_value="2026-04-02T10:05:00+00:00",
    )
    def test_pause_success(self, _mock_time, _mock_uuid):
        session = _make_session(state=SessionState.RECORDING)
        self.session_repo.find_active_by_consultation_id.return_value = session

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
        )

        self.assertEqual(result.state, SessionState.PAUSED)
        self.session_repo.update.assert_called_once()
        self.audit_repo.append.assert_called_once()
        audit = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit.event_type, AuditAction.SESSION_PAUSED)

    def test_pause_no_session(self):
        self.session_repo.find_active_by_consultation_id.return_value = None

        with self.assertRaises(SessionNotFoundError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
            )

    def test_pause_wrong_doctor(self):
        session = _make_session(doctor_id="doc-other")
        self.session_repo.find_active_by_consultation_id.return_value = session

        with self.assertRaises(SessionOwnershipError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
            )

    def test_pause_not_recording_raises(self):
        session = _make_session(state=SessionState.PAUSED)
        self.session_repo.find_active_by_consultation_id.return_value = session

        with self.assertRaises(SessionPauseRejectedError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
            )


class ResumeSessionUseCaseTest(unittest.TestCase):
    def setUp(self):
        self.session_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.session.resume_session import ResumeSessionUseCase

        self.use_case = ResumeSessionUseCase(
            session_repo=self.session_repo,
            audit_repo=self.audit_repo,
        )

    @patch(
        "deskai.application.session.resume_session.new_uuid",
        return_value="evt-002",
    )
    @patch(
        "deskai.application.session.resume_session.utc_now_iso",
        return_value="2026-04-02T10:10:00+00:00",
    )
    def test_resume_success(self, _mock_time, _mock_uuid):
        session = _make_session(state=SessionState.PAUSED)
        self.session_repo.find_active_by_consultation_id.return_value = session

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
        )

        self.assertEqual(result.state, SessionState.RECORDING)
        self.session_repo.update.assert_called_once()
        self.audit_repo.append.assert_called_once()
        audit = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit.event_type, AuditAction.SESSION_RESUMED)

    def test_resume_no_session(self):
        self.session_repo.find_active_by_consultation_id.return_value = None

        with self.assertRaises(SessionNotFoundError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
            )

    def test_resume_not_paused_raises(self):
        session = _make_session(state=SessionState.RECORDING)
        self.session_repo.find_active_by_consultation_id.return_value = session

        with self.assertRaises(SessionPauseRejectedError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
            )


if __name__ == "__main__":
    unittest.main()
