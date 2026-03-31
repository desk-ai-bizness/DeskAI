"""Unit tests for the get current user use case."""

import unittest
from unittest.mock import MagicMock

from deskai.application.auth.get_current_user import (
    GetCurrentUserUseCase,
)
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.exceptions import (
    DoctorProfileNotFoundError,
)
from deskai.domain.auth.value_objects import PlanType


class GetCurrentUserUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_repo = MagicMock()
        self.use_case = GetCurrentUserUseCase(
            doctor_repo=self.mock_repo,
        )

    def test_returns_profile_when_found(self) -> None:
        profile = DoctorProfile(
            doctor_id="d1",
            cognito_sub="sub-1",
            email="doc@test.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic",
            plan_type=PlanType.PLUS,
            created_at="2026-01-01T00:00:00+00:00",
        )
        self.mock_repo.find_by_cognito_sub.return_value = (
            profile
        )
        result = self.use_case.execute("sub-1")
        self.assertEqual(result, profile)

    def test_raises_when_not_found(self) -> None:
        self.mock_repo.find_by_cognito_sub.return_value = None
        with self.assertRaises(DoctorProfileNotFoundError):
            self.use_case.execute("sub-missing")


if __name__ == "__main__":
    unittest.main()
