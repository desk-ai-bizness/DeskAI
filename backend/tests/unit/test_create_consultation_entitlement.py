"""Unit tests for plan entitlement enforcement on CreateConsultationUseCase."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.auth.exceptions import PlanLimitExceededError, TrialExpiredError
from deskai.domain.auth.value_objects import PlanType
from deskai.domain.consultation.entities import ConsultationStatus
from tests.conftest import make_sample_auth_context, make_sample_patient

_MOD = "deskai.application.consultation.create_consultation"

# A recent created_at that keeps the 14-day trial active when "now" is 2026-04-01
ACTIVE_TRIAL_CREATED_AT = "2026-03-25T00:00:00+00:00"
# An old created_at that makes the 14-day trial expired
EXPIRED_TRIAL_CREATED_AT = "2025-01-01T00:00:00+00:00"


class CreateConsultationEntitlementTest(unittest.TestCase):
    """Verify that plan entitlement is enforced before creating a consultation."""

    def setUp(self) -> None:
        self.consultation_repo = MagicMock()
        self.patient_repo = MagicMock()
        self.audit_repo = MagicMock()
        self.doctor_repo = MagicMock()

        from deskai.application.consultation.create_consultation import (
            CreateConsultationUseCase,
        )

        self.use_case = CreateConsultationUseCase(
            consultation_repo=self.consultation_repo,
            patient_repo=self.patient_repo,
            audit_repo=self.audit_repo,
            doctor_repo=self.doctor_repo,
        )
        self.patient_repo.find_by_id.return_value = make_sample_patient()

    # ------------------------------------------------------------------
    # Plan limit scenarios
    # ------------------------------------------------------------------

    def test_raises_plan_limit_exceeded_when_free_trial_at_limit(self) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.FREE_TRIAL)
        self.doctor_repo.count_consultations_this_month.return_value = 10
        self.doctor_repo.find_created_at.return_value = ACTIVE_TRIAL_CREATED_AT

        with self.assertRaises(PlanLimitExceededError):
            self.use_case.execute(
                auth_context=auth,
                patient_id="pat-001",
                specialty="general_practice",
                scheduled_date="2026-04-01",
            )

        self.consultation_repo.save.assert_not_called()

    def test_raises_plan_limit_exceeded_when_plus_at_limit(self) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.PLUS)
        self.doctor_repo.count_consultations_this_month.return_value = 50
        self.doctor_repo.find_created_at.return_value = "2026-01-15T10:00:00+00:00"

        with self.assertRaises(PlanLimitExceededError):
            self.use_case.execute(
                auth_context=auth,
                patient_id="pat-001",
                specialty="general_practice",
                scheduled_date="2026-04-01",
            )

        self.consultation_repo.save.assert_not_called()

    @patch(f"{_MOD}.new_uuid", return_value="cons-uuid-ent")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_allows_creation_when_free_trial_under_limit(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.FREE_TRIAL)
        self.doctor_repo.count_consultations_this_month.return_value = 5
        self.doctor_repo.find_created_at.return_value = ACTIVE_TRIAL_CREATED_AT

        result = self.use_case.execute(
            auth_context=auth,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )

        self.assertEqual(result.status, ConsultationStatus.STARTED)
        self.consultation_repo.save.assert_called_once()

    @patch(f"{_MOD}.new_uuid", return_value="cons-uuid-pro")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_allows_creation_for_pro_plan_unlimited(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.PRO)
        self.doctor_repo.count_consultations_this_month.return_value = 999
        self.doctor_repo.find_created_at.return_value = "2026-01-15T10:00:00+00:00"

        result = self.use_case.execute(
            auth_context=auth,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )

        self.assertEqual(result.status, ConsultationStatus.STARTED)
        self.consultation_repo.save.assert_called_once()

    @patch(f"{_MOD}.new_uuid", return_value="cons-uuid-plus")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_allows_creation_when_plus_under_limit(
        self, _mock_time: MagicMock, _mock_uuid: MagicMock
    ) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.PLUS)
        self.doctor_repo.count_consultations_this_month.return_value = 25
        self.doctor_repo.find_created_at.return_value = "2026-01-15T10:00:00+00:00"

        result = self.use_case.execute(
            auth_context=auth,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )

        self.assertEqual(result.status, ConsultationStatus.STARTED)
        self.consultation_repo.save.assert_called_once()

    # ------------------------------------------------------------------
    # Trial expired scenario
    # ------------------------------------------------------------------

    def test_raises_trial_expired_when_free_trial_over_14_days(self) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.FREE_TRIAL)
        self.doctor_repo.count_consultations_this_month.return_value = 0
        self.doctor_repo.find_created_at.return_value = EXPIRED_TRIAL_CREATED_AT

        with self.assertRaises(TrialExpiredError):
            self.use_case.execute(
                auth_context=auth,
                patient_id="pat-001",
                specialty="general_practice",
                scheduled_date="2026-04-01",
            )

        self.consultation_repo.save.assert_not_called()

    # ------------------------------------------------------------------
    # Entitlement check happens before patient lookup
    # ------------------------------------------------------------------

    def test_entitlement_check_happens_before_patient_lookup(self) -> None:
        """When plan limit is exceeded, patient lookup should not happen."""
        auth = make_sample_auth_context(plan_type=PlanType.FREE_TRIAL)
        self.doctor_repo.count_consultations_this_month.return_value = 10
        self.doctor_repo.find_created_at.return_value = ACTIVE_TRIAL_CREATED_AT

        with self.assertRaises(PlanLimitExceededError):
            self.use_case.execute(
                auth_context=auth,
                patient_id="pat-001",
                specialty="general_practice",
                scheduled_date="2026-04-01",
            )

        self.patient_repo.find_by_id.assert_not_called()


if __name__ == "__main__":
    unittest.main()
