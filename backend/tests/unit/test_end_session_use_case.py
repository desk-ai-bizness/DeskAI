"""Unit tests for the EndSession use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import (
    InvalidSessionStateError,
    SessionNotFoundError,
)
from tests.conftest import make_sample_consultation

_MOD = "deskai.application.session.end_session"


class EndSessionUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.session_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.session.end_session import EndSessionUseCase

        self.use_case = EndSessionUseCase(
            consultation_repo=self.consultation_repo,
            session_repo=self.session_repo,
            audit_repo=self.audit_repo,
        )

    def _make_active_session(
        self,
        session_id: str = "sess-001",
        started_at: str = "2026-04-02T09:00:00+00:00",
    ) -> Session:
        return Session(
            session_id=session_id,
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ACTIVE,
            started_at=started_at,
            audio_chunks_received=42,
        )

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T10:00:00+00:00")
    def test_end_session_success(self, _mock_time: MagicMock, _mock_uuid: MagicMock) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.RECORDING)
        self.consultation_repo.find_by_id.return_value = consultation

        active_session = self._make_active_session()
        self.session_repo.find_active_by_consultation_id.return_value = active_session

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.session_id, "sess-001")
        self.assertEqual(result.state, SessionState.ENDED)
        self.assertEqual(result.ended_at, "2026-04-02T10:00:00+00:00")
        self.session_repo.update.assert_called_once()
        self.consultation_repo.save.assert_called_once()
        saved_consultation = self.consultation_repo.save.call_args[0][0]
        self.assertEqual(saved_consultation.status, ConsultationStatus.IN_PROCESSING)
        self.assertEqual(saved_consultation.session_ended_at, "2026-04-02T10:00:00+00:00")
        self.assertEqual(saved_consultation.processing_started_at, "2026-04-02T10:00:00+00:00")

    def test_end_session_consultation_not_found(self) -> None:
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute(
                consultation_id="cons-missing",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    def test_end_session_wrong_doctor(self) -> None:
        consultation = make_sample_consultation(doctor_id="doc-other")
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    def test_end_session_idempotent_when_already_processing(self) -> None:
        consultation = make_sample_consultation(
            status=ConsultationStatus.IN_PROCESSING,
            session_ended_at="2026-04-02T09:30:00+00:00",
        )
        self.consultation_repo.find_by_id.return_value = consultation

        ended_session = Session(
            session_id="sess-001",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ENDED,
            started_at="2026-04-02T09:00:00+00:00",
            ended_at="2026-04-02T09:30:00+00:00",
        )
        self.session_repo.find_active_by_consultation_id.return_value = ended_session

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.session_id, "sess-001")
        self.session_repo.update.assert_not_called()
        self.consultation_repo.save.assert_not_called()

    def test_end_session_no_active_session(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.RECORDING)
        self.consultation_repo.find_by_id.return_value = consultation
        self.session_repo.find_active_by_consultation_id.return_value = None

        with self.assertRaises(SessionNotFoundError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    def test_end_session_already_ended(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.RECORDING)
        self.consultation_repo.find_by_id.return_value = consultation

        ended_session = Session(
            session_id="sess-001",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ENDED,
            started_at="2026-04-02T09:00:00+00:00",
            ended_at="2026-04-02T09:30:00+00:00",
        )
        self.session_repo.find_active_by_consultation_id.return_value = ended_session

        with self.assertRaises(InvalidSessionStateError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T10:00:00+00:00")
    def test_end_session_creates_audit_event(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.RECORDING)
        self.consultation_repo.find_by_id.return_value = consultation
        active_session = self._make_active_session()
        self.session_repo.find_active_by_consultation_id.return_value = active_session

        self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.audit_repo.append.assert_called_once()
        audit_event = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit_event.consultation_id, "cons-001")
        self.assertEqual(audit_event.event_type, AuditAction.SESSION_ENDED)
        self.assertEqual(audit_event.actor_id, "doc-001")

    @patch(f"{_MOD}.new_uuid", side_effect=["evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T10:00:00+00:00")
    def test_end_session_computes_duration(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.RECORDING)
        self.consultation_repo.find_by_id.return_value = consultation

        active_session = self._make_active_session(
            started_at="2026-04-02T09:45:00+00:00"
        )
        self.session_repo.find_active_by_consultation_id.return_value = active_session

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.duration_seconds, 900)


if __name__ == "__main__":
    unittest.main()
