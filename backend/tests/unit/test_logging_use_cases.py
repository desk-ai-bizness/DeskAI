"""Tests for use case logging behavior.

Verifies that application-layer use cases emit the correct structured
log events at the correct levels.
"""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.auth.exceptions import TrialExpiredError
from deskai.domain.auth.value_objects import AuthContext, PlanType
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.patient.entities import Patient
from deskai.domain.patient.exceptions import PatientNotFoundError
from deskai.domain.session.entities import Session, SessionState


class CreateConsultationLoggingTest(unittest.TestCase):
    """Verify CreateConsultationUseCase emits correct log events."""

    _LOGGER_NAME = "deskai-backend"

    def _make_use_case(self):
        from deskai.application.consultation.create_consultation import (
            CreateConsultationUseCase,
        )

        return CreateConsultationUseCase(
            consultation_repo=MagicMock(),
            patient_repo=MagicMock(),
            audit_repo=MagicMock(),
            doctor_repo=MagicMock(),
        )

    def _make_auth_context(self) -> AuthContext:
        return AuthContext(
            doctor_id="doc-1",
            email="doc@clinic.com",
            clinic_id="clinic-1",
            plan_type=PlanType.PLUS,
        )

    @patch(
        "deskai.application.consultation.create_consultation.new_uuid",
        return_value="cons-new",
    )
    @patch(
        "deskai.application.consultation.create_consultation.utc_now_iso",
        return_value="2026-04-03T10:00:00+00:00",
    )
    def test_successful_creation_logs_started_and_created(
        self, _mock_time, _mock_uuid,
    ) -> None:
        uc = self._make_use_case()
        uc.doctor_repo.count_consultations_this_month.return_value = 0
        uc.doctor_repo.find_created_at.return_value = None
        uc.patient_repo.find_by_id.return_value = Patient(
            patient_id="pat-1", name="Test", cpf="52998224725", date_of_birth="1990-01-01",
            clinic_id="clinic-1", created_at="2026-01-01T00:00:00+00:00",
        )

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            uc.execute(self._make_auth_context(), "pat-1", "general", "2026-04-03")

        messages = [r.getMessage() for r in cm.records]
        self.assertTrue(
            any("consultation_creation_started" in m for m in messages),
            f"Expected 'consultation_creation_started' in {messages}",
        )
        self.assertTrue(
            any("consultation_created" in m for m in messages),
            f"Expected 'consultation_created' in {messages}",
        )

    def test_trial_expired_logs_blocked(self) -> None:
        uc = self._make_use_case()
        uc.doctor_repo.count_consultations_this_month.return_value = 0
        # Simulate expired trial by returning a very old created_at
        from datetime import UTC, datetime, timedelta
        old_date = datetime.now(tz=UTC) - timedelta(days=400)
        uc.doctor_repo.find_created_at.return_value = old_date

        auth = AuthContext(
            doctor_id="doc-1", email="doc@clinic.com",
            clinic_id="clinic-1", plan_type=PlanType.FREE_TRIAL,
        )

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            with self.assertRaises(TrialExpiredError):
                uc.execute(auth, "pat-1", "general", "2026-04-03")

        messages = [r.getMessage() for r in cm.records]
        self.assertTrue(
            any("consultation_creation_blocked" in m for m in messages),
            f"Expected 'consultation_creation_blocked' in {messages}",
        )

    def test_patient_not_found_logs_failed(self) -> None:
        uc = self._make_use_case()
        uc.doctor_repo.count_consultations_this_month.return_value = 0
        uc.doctor_repo.find_created_at.return_value = None
        uc.patient_repo.find_by_id.return_value = None

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            with self.assertRaises(PatientNotFoundError):
                uc.execute(self._make_auth_context(), "pat-missing", "general", "2026-04-03")

        messages = [r.getMessage() for r in cm.records]
        self.assertTrue(
            any("consultation_creation_failed" in m for m in messages),
            f"Expected 'consultation_creation_failed' in {messages}",
        )


class StartSessionLoggingTest(unittest.TestCase):
    """Verify StartSessionUseCase emits correct log events."""

    _LOGGER_NAME = "deskai-backend"

    def _make_use_case(self):
        from deskai.application.session.start_session import StartSessionUseCase

        return StartSessionUseCase(
            consultation_repo=MagicMock(),
            session_repo=MagicMock(),
            audit_repo=MagicMock(),
        )

    def _make_consultation(self, status=ConsultationStatus.STARTED) -> Consultation:
        return Consultation(
            consultation_id="cons-1",
            clinic_id="clinic-1",
            doctor_id="doc-1",
            patient_id="pat-1",
            specialty="general",
            status=status,
            scheduled_date="2026-04-03",
            notes="",
            created_at="2026-04-03T10:00:00+00:00",
            updated_at="2026-04-03T10:00:00+00:00",
        )

    @patch(
        "deskai.application.session.start_session.new_uuid",
        return_value="sess-new",
    )
    @patch(
        "deskai.application.session.start_session.utc_now_iso",
        return_value="2026-04-03T10:00:00+00:00",
    )
    def test_start_session_logs_requested_and_started(
        self, _mock_time, _mock_uuid,
    ) -> None:
        uc = self._make_use_case()
        uc.consultation_repo.find_by_id.return_value = self._make_consultation()
        uc.session_repo.find_active_by_consultation_id.return_value = None

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            uc.execute("cons-1", "doc-1", "clinic-1")

        messages = [r.getMessage() for r in cm.records]
        self.assertTrue(
            any("session_start_requested" in m for m in messages),
            f"Expected 'session_start_requested' in {messages}",
        )
        self.assertTrue(
            any("session_started" in m for m in messages),
            f"Expected 'session_started' in {messages}",
        )

    def test_idempotent_start_logs_idempotent(self) -> None:
        uc = self._make_use_case()
        uc.consultation_repo.find_by_id.return_value = self._make_consultation(
            status=ConsultationStatus.RECORDING,
        )
        existing_session = Session(
            session_id="sess-existing",
            consultation_id="cons-1",
            doctor_id="doc-1",
            clinic_id="clinic-1",
            state=SessionState.RECORDING,
            started_at="2026-04-03T10:00:00+00:00",
        )
        uc.session_repo.find_active_by_consultation_id.return_value = existing_session

        with self.assertLogs(self._LOGGER_NAME, level="DEBUG") as cm:
            result = uc.execute("cons-1", "doc-1", "clinic-1")

        self.assertEqual(result.session_id, "sess-existing")
        messages = [r.getMessage() for r in cm.records]
        self.assertTrue(
            any("session_start_idempotent" in m for m in messages),
            f"Expected 'session_start_idempotent' in {messages}",
        )


if __name__ == "__main__":
    unittest.main()
