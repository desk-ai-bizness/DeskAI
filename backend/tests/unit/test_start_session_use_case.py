"""Unit tests for the StartSession use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import InvalidSessionStateError
from tests.conftest import make_sample_consultation

_MOD = "deskai.application.session.start_session"


class StartSessionUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.session_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.session.start_session import StartSessionUseCase

        self.use_case = StartSessionUseCase(
            consultation_repo=self.consultation_repo,
            session_repo=self.session_repo,
            audit_repo=self.audit_repo,
        )

    @patch(f"{_MOD}.new_uuid", return_value="sess-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T10:00:00+00:00")
    def test_start_session_success(self, _mock_time: MagicMock, _mock_uuid: MagicMock) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.STARTED)
        self.consultation_repo.find_by_id.return_value = consultation
        self.session_repo.find_active_by_consultation_id.return_value = None

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.session_id, "sess-uuid-1")
        self.assertEqual(result.consultation_id, "cons-001")
        self.assertEqual(result.doctor_id, "doc-001")
        self.assertEqual(result.clinic_id, "clinic-001")
        self.assertEqual(result.state, SessionState.ACTIVE)
        self.assertEqual(result.started_at, "2026-04-02T10:00:00+00:00")
        self.session_repo.save.assert_called_once()
        self.consultation_repo.save.assert_called_once()
        saved_consultation = self.consultation_repo.save.call_args[0][0]
        self.assertEqual(saved_consultation.status, ConsultationStatus.RECORDING)
        self.assertEqual(saved_consultation.session_started_at, "2026-04-02T10:00:00+00:00")

    def test_start_session_consultation_not_found(self) -> None:
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute(
                consultation_id="cons-missing",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    def test_start_session_wrong_doctor(self) -> None:
        consultation = make_sample_consultation(doctor_id="doc-other")
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    @patch(f"{_MOD}.new_uuid", return_value="sess-uuid-2")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T10:00:00+00:00")
    def test_start_session_idempotent_when_recording(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.RECORDING)
        self.consultation_repo.find_by_id.return_value = consultation

        existing_session = Session(
            session_id="sess-existing",
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
            state=SessionState.ACTIVE,
            started_at="2026-04-02T09:00:00+00:00",
        )
        self.session_repo.find_active_by_consultation_id.return_value = existing_session

        result = self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.session_id, "sess-existing")
        self.session_repo.save.assert_not_called()
        self.consultation_repo.save.assert_not_called()

    def test_start_session_invalid_status(self) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.IN_PROCESSING)
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(InvalidSessionStateError):
            self.use_case.execute(
                consultation_id="cons-001",
                doctor_id="doc-001",
                clinic_id="clinic-001",
            )

    @patch(f"{_MOD}.new_uuid", side_effect=["sess-uuid-3", "evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T10:00:00+00:00")
    def test_start_session_creates_audit_event(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        consultation = make_sample_consultation(status=ConsultationStatus.STARTED)
        self.consultation_repo.find_by_id.return_value = consultation
        self.session_repo.find_active_by_consultation_id.return_value = None

        self.use_case.execute(
            consultation_id="cons-001",
            doctor_id="doc-001",
            clinic_id="clinic-001",
        )

        self.audit_repo.append.assert_called_once()
        audit_event = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit_event.event_id, "evt-uuid-1")
        self.assertEqual(audit_event.consultation_id, "cons-001")
        self.assertEqual(audit_event.event_type, AuditAction.SESSION_STARTED)
        self.assertEqual(audit_event.actor_id, "doc-001")


if __name__ == "__main__":
    unittest.main()
