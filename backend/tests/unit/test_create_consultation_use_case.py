"""Unit tests for the CreateConsultation use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.audit.entities import AuditAction
from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.patient.exceptions import PatientNotFoundError, PatientValidationError
from tests.conftest import make_sample_auth_context, make_sample_patient

_MOD = "deskai.application.consultation.create_consultation"


class CreateConsultationUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.patient_repo = MagicMock()
        self.audit_repo = MagicMock()

        from deskai.application.consultation.create_consultation import (
            CreateConsultationUseCase,
        )

        self.use_case = CreateConsultationUseCase(
            consultation_repo=self.consultation_repo,
            patient_repo=self.patient_repo,
            audit_repo=self.audit_repo,
        )
        self.auth_context = make_sample_auth_context()

    @patch(f"{_MOD}.new_uuid", return_value="cons-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_creates_consultation_with_valid_inputs(self, _mock_time, _mock_uuid) -> None:
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        result = self.use_case.execute(
            auth_context=self.auth_context,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
            notes="Initial visit",
        )

        self.assertEqual(result.consultation_id, "cons-uuid-1")
        self.assertEqual(result.patient_id, "pat-001")
        self.assertEqual(result.doctor_id, "doc-001")
        self.assertEqual(result.clinic_id, "clinic-001")
        self.assertEqual(result.specialty, "general_practice")
        self.assertEqual(result.status, ConsultationStatus.STARTED)
        self.assertEqual(result.scheduled_date, "2026-04-01")
        self.assertEqual(result.notes, "Initial visit")

    def test_raises_when_patient_not_found(self) -> None:
        self.patient_repo.find_by_id.return_value = None

        with self.assertRaises(PatientNotFoundError):
            self.use_case.execute(
                auth_context=self.auth_context,
                patient_id="pat-missing",
                specialty="general_practice",
                scheduled_date="2026-04-01",
            )

    @patch(f"{_MOD}.new_uuid", return_value="cons-uuid-2")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_saves_consultation_to_repo(self, _mock_time, _mock_uuid) -> None:
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        self.use_case.execute(
            auth_context=self.auth_context,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )

        self.consultation_repo.save.assert_called_once()
        saved = self.consultation_repo.save.call_args[0][0]
        self.assertEqual(saved.consultation_id, "cons-uuid-2")

    @patch(f"{_MOD}.new_uuid", side_effect=["cons-uuid-3", "evt-uuid-1"])
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_creates_audit_event(self, _mock_time, _mock_uuid) -> None:
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        self.use_case.execute(
            auth_context=self.auth_context,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )

        self.audit_repo.append.assert_called_once()
        audit_event = self.audit_repo.append.call_args[0][0]
        self.assertEqual(audit_event.event_id, "evt-uuid-1")
        self.assertEqual(audit_event.consultation_id, "cons-uuid-3")
        self.assertEqual(audit_event.event_type, AuditAction.CONSULTATION_CREATED)
        self.assertEqual(audit_event.actor_id, "doc-001")

    @patch(f"{_MOD}.new_uuid", return_value="cons-uuid-4")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_returns_consultation_with_started_status(self, _mock_time, _mock_uuid) -> None:
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        result = self.use_case.execute(
            auth_context=self.auth_context,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )

        self.assertEqual(result.status, ConsultationStatus.STARTED)

    def test_validates_required_fields(self) -> None:
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        with self.assertRaises(PatientValidationError):
            self.use_case.execute(
                auth_context=self.auth_context,
                patient_id="",
                specialty="general_practice",
                scheduled_date="2026-04-01",
            )


if __name__ == "__main__":
    unittest.main()
