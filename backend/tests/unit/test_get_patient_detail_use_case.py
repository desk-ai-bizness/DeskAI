"""Unit tests for the patient detail/history use case."""

import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.patient.exceptions import PatientNotFoundError
from tests.conftest import (
    make_sample_auth_context,
    make_sample_consultation,
    make_sample_patient,
)


class GetPatientDetailUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        from deskai.application.patient.get_patient_detail import (
            GetPatientDetailUseCase,
        )

        self.patient_repo = MagicMock()
        self.consultation_repo = MagicMock()
        self.artifact_repo = MagicMock()
        self.use_case = GetPatientDetailUseCase(
            patient_repo=self.patient_repo,
            consultation_repo=self.consultation_repo,
            artifact_repo=self.artifact_repo,
        )
        self.auth_context = make_sample_auth_context(doctor_id="doc-001", clinic_id="clinic-001")

    def test_returns_patient_and_current_doctor_history(self) -> None:
        patient = make_sample_patient(patient_id="pat-001")
        consultation = make_sample_consultation(
            consultation_id="cons-001",
            patient_id="pat-001",
            doctor_id="doc-001",
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-02T12:00:00+00:00",
        )
        self.patient_repo.find_by_id.return_value = patient
        self.consultation_repo.find_by_patient_for_doctor.return_value = [consultation]
        self.artifact_repo.get_artifact.return_value = {
            "summary": {"content": "Paciente retornou para acompanhamento."}
        }

        result = self.use_case.execute(self.auth_context, patient_id="pat-001")

        self.assertEqual(result.patient, patient)
        self.assertEqual(len(result.history), 1)
        self.assertEqual(result.history[0].consultation.consultation_id, "cons-001")
        self.assertEqual(result.history[0].preview, {
            "summary": "Paciente retornou para acompanhamento."
        })
        self.consultation_repo.find_by_patient_for_doctor.assert_called_once_with(
            clinic_id="clinic-001",
            patient_id="pat-001",
            doctor_id="doc-001",
        )
        self.artifact_repo.get_artifact.assert_called_once_with(
            "clinic-001",
            "cons-001",
            ArtifactType.FINAL_VERSION,
        )

    def test_raises_when_patient_not_in_clinic(self) -> None:
        self.patient_repo.find_by_id.return_value = None

        with self.assertRaises(PatientNotFoundError):
            self.use_case.execute(self.auth_context, patient_id="pat-missing")

        self.consultation_repo.find_by_patient_for_doctor.assert_not_called()

    def test_does_not_load_preview_for_non_finalized_consultation(self) -> None:
        patient = make_sample_patient(patient_id="pat-001")
        consultation = make_sample_consultation(
            consultation_id="cons-001",
            patient_id="pat-001",
            doctor_id="doc-001",
            status=ConsultationStatus.STARTED,
        )
        self.patient_repo.find_by_id.return_value = patient
        self.consultation_repo.find_by_patient_for_doctor.return_value = [consultation]

        result = self.use_case.execute(self.auth_context, patient_id="pat-001")

        self.assertIsNone(result.history[0].preview)
        self.artifact_repo.get_artifact.assert_not_called()


if __name__ == "__main__":
    unittest.main()
