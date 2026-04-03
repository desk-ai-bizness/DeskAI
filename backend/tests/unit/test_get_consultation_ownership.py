"""Unit tests for doctor_id ownership check on GetConsultationUseCase."""

import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from tests.conftest import make_sample_auth_context, make_sample_consultation


class GetConsultationOwnershipTest(unittest.TestCase):
    """Verify that GetConsultationUseCase enforces doctor_id ownership."""

    def setUp(self) -> None:
        self.consultation_repo = MagicMock()

        from deskai.application.consultation.get_consultation import (
            GetConsultationUseCase,
        )

        self.use_case = GetConsultationUseCase(
            consultation_repo=self.consultation_repo,
        )

    def test_returns_consultation_when_doctor_owns_it(self) -> None:
        auth = make_sample_auth_context(doctor_id="doc-001")
        consultation = make_sample_consultation(doctor_id="doc-001")
        self.consultation_repo.find_by_id.return_value = consultation

        result = self.use_case.execute(
            auth_context=auth,
            consultation_id="cons-001",
            clinic_id="clinic-001",
        )

        self.assertEqual(result.consultation_id, "cons-001")

    def test_raises_ownership_error_when_doctor_does_not_own(self) -> None:
        auth = make_sample_auth_context(doctor_id="doc-other")
        consultation = make_sample_consultation(doctor_id="doc-001")
        self.consultation_repo.find_by_id.return_value = consultation

        with self.assertRaises(ConsultationOwnershipError):
            self.use_case.execute(
                auth_context=auth,
                consultation_id="cons-001",
                clinic_id="clinic-001",
            )

    def test_raises_not_found_before_ownership_check(self) -> None:
        auth = make_sample_auth_context(doctor_id="doc-other")
        self.consultation_repo.find_by_id.return_value = None

        with self.assertRaises(ConsultationNotFoundError):
            self.use_case.execute(
                auth_context=auth,
                consultation_id="cons-missing",
                clinic_id="clinic-001",
            )


if __name__ == "__main__":
    unittest.main()
