"""Unit tests for the patient domain."""

import unittest

from deskai.domain.patient.entities import Patient
from deskai.domain.patient.exceptions import PatientNotFoundError, PatientValidationError


class PatientEntityTest(unittest.TestCase):
    def test_create_patient_with_all_fields(self) -> None:
        p = Patient(
            patient_id="pat-001",
            name="Maria Silva",
            date_of_birth="1990-05-15",
            clinic_id="clinic-1",
            created_at="2026-03-20T10:00:00+00:00",
        )
        self.assertEqual(p.patient_id, "pat-001")
        self.assertEqual(p.name, "Maria Silva")
        self.assertEqual(p.date_of_birth, "1990-05-15")
        self.assertEqual(p.clinic_id, "clinic-1")
        self.assertEqual(p.created_at, "2026-03-20T10:00:00+00:00")

    def test_patient_is_frozen(self) -> None:
        p = Patient(
            patient_id="pat-001",
            name="Maria Silva",
            date_of_birth="1990-05-15",
            clinic_id="clinic-1",
            created_at="2026-03-20T10:00:00+00:00",
        )
        with self.assertRaises(AttributeError):
            p.name = "New Name"  # type: ignore[misc]


class PatientExceptionsTest(unittest.TestCase):
    def test_patient_not_found_error_is_deskai_error(self) -> None:
        from deskai.shared.errors import DeskAIError

        err = PatientNotFoundError("Patient pat-001 not found")
        self.assertIsInstance(err, DeskAIError)

    def test_patient_validation_error_is_deskai_error(self) -> None:
        from deskai.shared.errors import DeskAIError

        err = PatientValidationError("Invalid patient data")
        self.assertIsInstance(err, DeskAIError)


if __name__ == "__main__":
    unittest.main()
