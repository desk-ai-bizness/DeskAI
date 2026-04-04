"""Unit tests for auth domain entities."""

import unittest
from datetime import UTC, datetime

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import PlanType


class DoctorProfileTest(unittest.TestCase):
    def test_doctor_profile_is_frozen(self) -> None:
        p = DoctorProfile(
            doctor_id="d1",
            identity_provider_id="sub-1",
            email="doc@clinic.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic One",
            plan_type=PlanType.FREE_TRIAL,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        with self.assertRaises(AttributeError):
            p.name = "Dr. Other"

    def test_doctor_profile_fields(self) -> None:
        p = DoctorProfile(
            doctor_id="d1",
            identity_provider_id="sub-1",
            email="doc@clinic.com",
            name="Dr. Test",
            clinic_id="c1",
            clinic_name="Clinic One",
            plan_type=PlanType.PLUS,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.assertEqual(p.plan_type, PlanType.PLUS)
        self.assertEqual(p.clinic_name, "Clinic One")


if __name__ == "__main__":
    unittest.main()
