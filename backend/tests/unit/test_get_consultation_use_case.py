"""Unit tests for the GetConsultation use case."""

import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.exceptions import ConsultationNotFoundError

from tests.conftest import make_sample_consultation


class GetConsultationUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()

        from deskai.application.consultation.get_consultation import (
            GetConsultationUseCase,
        )

        self.use_case = GetConsultationUseCase(
            consultation_repo=self.consultation_repo,
        )

    def test_returns_consultation_when_found(self) -> None:
        expected = make_sample_consultation()
        self.consultation_repo.find_by_id.return_value = expected

        result = self.use_case.execute("cons-001", "clinic-001")

        self.assertEqual(result.consultation_id, "cons-001")
        self.consultation_repo.find_by_id.assert_called_once_with("cons-001", "clinic-001")

    def test_raises_not_found_when_missing(self) -> None:
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute("cons-missing", "clinic-001")


if __name__ == "__main__":
    unittest.main()
