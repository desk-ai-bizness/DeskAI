"""Unit tests for the ListConsultations use case."""

import unittest
from unittest.mock import MagicMock

from tests.conftest import make_sample_consultation


class ListConsultationsUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()

        from deskai.application.consultation.list_consultations import (
            ListConsultationsUseCase,
        )

        self.use_case = ListConsultationsUseCase(
            consultation_repo=self.consultation_repo,
        )

    def test_returns_list_from_repo(self) -> None:
        expected = [
            make_sample_consultation(consultation_id="c1"),
            make_sample_consultation(consultation_id="c2"),
        ]
        self.consultation_repo.find_by_doctor_and_date_range.return_value = expected

        result = self.use_case.execute(doctor_id="doc-001")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].consultation_id, "c1")
        self.assertEqual(result[1].consultation_id, "c2")

    def test_passes_date_range_to_repo(self) -> None:
        self.consultation_repo.find_by_doctor_and_date_range.return_value = []

        self.use_case.execute(
            doctor_id="doc-001",
            start_date="2026-04-01",
            end_date="2026-04-30",
        )

        self.consultation_repo.find_by_doctor_and_date_range.assert_called_once_with(
            "doc-001", "2026-04-01", "2026-04-30"
        )


if __name__ == "__main__":
    unittest.main()
