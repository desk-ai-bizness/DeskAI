"""Unit tests for the ListPatients use case."""

import unittest
from unittest.mock import MagicMock

from tests.conftest import make_sample_patient


class ListPatientsUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.patient_repo = MagicMock()

        from deskai.application.patient.list_patients import (
            ListPatientsUseCase,
        )

        self.use_case = ListPatientsUseCase(
            patient_repo=self.patient_repo,
        )

    def test_returns_patients_from_repo(self) -> None:
        expected = [
            make_sample_patient(patient_id="p1"),
            make_sample_patient(patient_id="p2"),
        ]
        self.patient_repo.find_by_clinic.return_value = expected

        result = self.use_case.execute(clinic_id="clinic-001")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].patient_id, "p1")

    def test_passes_search_term_to_repo(self) -> None:
        self.patient_repo.find_by_clinic.return_value = []

        self.use_case.execute(clinic_id="clinic-001", search_term="Silva")

        self.patient_repo.find_by_clinic.assert_called_once_with(
            "clinic-001", "Silva"
        )


if __name__ == "__main__":
    unittest.main()
