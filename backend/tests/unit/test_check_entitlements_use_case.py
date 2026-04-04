"""Unit tests for the check entitlements use case."""

import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from deskai.application.auth.check_entitlements import (
    CheckEntitlementsUseCase,
)
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import PlanType


def _recent_datetime() -> datetime:
    """Return a datetime from 1 day ago — always within trial window."""
    return datetime.now(tz=UTC) - timedelta(days=1)


class CheckEntitlementsUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_repo = MagicMock()
        self.use_case = CheckEntitlementsUseCase(
            doctor_repo=self.mock_repo,
        )

    def _make_profile(self, plan: PlanType = PlanType.FREE_TRIAL) -> DoctorProfile:
        return DoctorProfile(
            doctor_id="d1",
            identity_provider_id="sub-1",
            email="doc@test.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic",
            plan_type=plan,
            created_at=_recent_datetime(),
        )

    def test_free_trial_with_remaining(self) -> None:
        self.mock_repo.count_consultations_this_month.return_value = 5
        e = self.use_case.execute(self._make_profile())
        self.assertTrue(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 5)

    def test_free_trial_at_limit(self) -> None:
        self.mock_repo.count_consultations_this_month.return_value = 10
        e = self.use_case.execute(self._make_profile())
        self.assertFalse(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, 0)

    def test_pro_unlimited(self) -> None:
        self.mock_repo.count_consultations_this_month.return_value = 999
        e = self.use_case.execute(self._make_profile(PlanType.PRO))
        self.assertTrue(e.can_create_consultation)
        self.assertEqual(e.consultations_remaining, -1)


if __name__ == "__main__":
    unittest.main()
