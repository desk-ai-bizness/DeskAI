"""Tests for doctor ownership check in GetConsultationUseCase."""

import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from tests.conftest import make_sample_auth_context, make_sample_consultation


class GetConsultationOwnershipTest(unittest.TestCase):
    def setUp(self) -> None:
        self.consultation_repo = MagicMock()

        from deskai.application.consultation.get_consultation import (
            GetConsultationUseCase,
        )

        self.use_case = GetConsultationUseCase(
            consultation_repo=self.consultation_repo,
        )
        self.auth_context = make_sample_auth_context()

    def test_doctor_owns_consultation_succeeds(self) -> None:
        consultation = make_sample_consultation(doctor_id="doc-001")
        self.consultation_repo.find_by_id.return_value = consultation

        result = self.use_case.execute(self.auth_context, "cons-001", "clinic-001")

        self.assertEqual(result.consultation_id, "cons-001")

    def test_doctor_does_not_own_raises(self) -> None:
        consultation = make_sample_consultation(doctor_id="other-doc")
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(self.auth_context, "cons-001", "clinic-001")

    def test_not_found_before_ownership_check(self) -> None:
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute(self.auth_context, "cons-missing", "clinic-001")


if __name__ == "__main__":
    unittest.main()
