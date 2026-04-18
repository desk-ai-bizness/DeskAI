"""Unit tests for the CreatePatient use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.patient.exceptions import PatientDuplicateCpfError, PatientValidationError
from tests.conftest import make_sample_auth_context

_MOD = "deskai.application.patient.create_patient"


class CreatePatientUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.patient_repo = MagicMock()
        self.patient_repo.find_by_cpf.return_value = None

        from deskai.application.patient.create_patient import (
            CreatePatientUseCase,
        )

        self.use_case = CreatePatientUseCase(
            patient_repo=self.patient_repo,
        )
        self.auth_context = make_sample_auth_context()

    @patch(f"{_MOD}.new_uuid", return_value="pat-uuid-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_creates_patient_with_valid_inputs(self, _mock_time, _mock_uuid) -> None:
        result = self.use_case.execute(
            auth_context=self.auth_context,
            name="Joao Silva",
            cpf="529.982.247-25",
            date_of_birth=None,
        )

        self.assertEqual(result.patient_id, "pat-uuid-1")
        self.assertEqual(result.name, "Joao Silva")
        self.assertEqual(result.cpf, "52998224725")
        self.assertIsNone(result.date_of_birth)
        self.assertEqual(result.clinic_id, "clinic-001")

    def test_raises_when_name_missing(self) -> None:
        with self.assertRaises(PatientValidationError):
            self.use_case.execute(
                auth_context=self.auth_context,
                name="",
                cpf="529.982.247-25",
                date_of_birth="1990-05-15",
            )

    def test_raises_when_name_whitespace_only(self) -> None:
        with self.assertRaises(PatientValidationError):
            self.use_case.execute(
                auth_context=self.auth_context,
                name="   ",
                cpf="529.982.247-25",
                date_of_birth="1990-05-15",
            )

    def test_raises_when_cpf_missing(self) -> None:
        with self.assertRaises(PatientValidationError):
            self.use_case.execute(
                auth_context=self.auth_context,
                name="Joao Silva",
                cpf="",
                date_of_birth="",
            )

    def test_raises_when_cpf_already_exists_in_clinic(self) -> None:
        self.patient_repo.find_by_cpf.return_value = object()

        with self.assertRaises(PatientDuplicateCpfError):
            self.use_case.execute(
                auth_context=self.auth_context,
                name="Joao Silva",
                cpf="529.982.247-25",
                date_of_birth=None,
            )

        self.patient_repo.save.assert_not_called()

    @patch(f"{_MOD}.new_uuid", return_value="pat-uuid-2")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_saves_to_repo(self, _mock_time, _mock_uuid) -> None:
        self.use_case.execute(
            auth_context=self.auth_context,
            name="Joao Silva",
            cpf="529.982.247-25",
            date_of_birth="1990-05-15",
        )

        self.patient_repo.save.assert_called_once()
        saved = self.patient_repo.save.call_args[0][0]
        self.assertEqual(saved.patient_id, "pat-uuid-2")
        self.assertEqual(saved.name, "Joao Silva")
        self.assertEqual(saved.cpf, "52998224725")


if __name__ == "__main__":
    unittest.main()
