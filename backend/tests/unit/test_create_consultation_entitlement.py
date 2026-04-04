"""Tests for plan entitlement enforcement in CreateConsultationUseCase."""

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from deskai.domain.auth.exceptions import PlanLimitExceededError, TrialExpiredError
from deskai.domain.auth.value_objects import PlanType
from tests.conftest import make_sample_auth_context, make_sample_patient

_MOD = "deskai.application.consultation.create_consultation"

ACTIVE_TRIAL_CREATED_AT = datetime(2026, 3, 25, tzinfo=UTC)
EXPIRED_TRIAL_CREATED_AT = datetime(2025, 1, 1, tzinfo=UTC)


class CreateConsultationEntitlementTest(unittest.TestCase):
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

    @patch(f"{_MOD}.new_uuid", return_value="cons-ent-1")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_free_trial_at_limit_raises(self, _t, _u) -> None:
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

    @patch(f"{_MOD}.new_uuid", return_value="cons-ent-2")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_plus_at_limit_raises(self, _t, _u) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.PLUS)
        self.doctor_repo.count_consultations_this_month.return_value = 50
        self.doctor_repo.find_created_at.return_value = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)

        with self.assertRaises(PlanLimitExceededError):
            self.use_case.execute(
                auth_context=auth,
                patient_id="pat-001",
                specialty="general_practice",
                scheduled_date="2026-04-01",
            )

    @patch(f"{_MOD}.new_uuid", return_value="cons-ent-3")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_free_trial_under_limit_succeeds(self, _t, _u) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.FREE_TRIAL)
        self.doctor_repo.count_consultations_this_month.return_value = 5
        self.doctor_repo.find_created_at.return_value = ACTIVE_TRIAL_CREATED_AT
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        result = self.use_case.execute(
            auth_context=auth,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )
        self.assertEqual(result.consultation_id, "cons-ent-3")

    @patch(f"{_MOD}.new_uuid", return_value="cons-ent-4")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_pro_plan_unlimited(self, _t, _u) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.PRO)
        self.doctor_repo.count_consultations_this_month.return_value = 999
        self.doctor_repo.find_created_at.return_value = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        result = self.use_case.execute(
            auth_context=auth,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )
        self.assertEqual(result.consultation_id, "cons-ent-4")

    @patch(f"{_MOD}.new_uuid", return_value="cons-ent-5")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_plus_under_limit_succeeds(self, _t, _u) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.PLUS)
        self.doctor_repo.count_consultations_this_month.return_value = 30
        self.doctor_repo.find_created_at.return_value = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)
        self.patient_repo.find_by_id.return_value = make_sample_patient()

        result = self.use_case.execute(
            auth_context=auth,
            patient_id="pat-001",
            specialty="general_practice",
            scheduled_date="2026-04-01",
        )
        self.assertEqual(result.consultation_id, "cons-ent-5")

    @patch(f"{_MOD}.new_uuid", return_value="cons-ent-6")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_trial_expired_raises(self, _t, _u) -> None:
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

    @patch(f"{_MOD}.new_uuid", return_value="cons-ent-7")
    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-01T10:00:00+00:00")
    def test_entitlement_checked_before_patient_lookup(self, _t, _u) -> None:
        auth = make_sample_auth_context(plan_type=PlanType.PLUS)
        self.doctor_repo.count_consultations_this_month.return_value = 50
        self.doctor_repo.find_created_at.return_value = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC)

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
