"""Unit tests for consultation business rules."""

import unittest

from deskai.domain.consultation.entities import ConsultationStatus
from deskai.domain.consultation.rules import can_finalize, validate_consultation_creation


def _make_consultation_with_status(status: ConsultationStatus):
    """Helper to create a minimal consultation-like object with a status."""
    from deskai.domain.consultation.entities import Consultation

    return Consultation(
        consultation_id="c-100",
        clinic_id="clinic-1",
        doctor_id="doc-1",
        patient_id="pat-1",
        specialty="general_practice",
        status=status,
    )


class ValidateConsultationCreationTest(unittest.TestCase):
    """Test validate_consultation_creation pure validator."""

    def test_valid_inputs_returns_empty_list(self) -> None:
        errors = validate_consultation_creation(
            patient_id="pat-1",
            doctor_id="doc-1",
            clinic_id="clinic-1",
            specialty="general_practice",
        )
        self.assertEqual(errors, [])

    def test_missing_patient_id_returns_error(self) -> None:
        errors = validate_consultation_creation(
            patient_id="",
            doctor_id="doc-1",
            clinic_id="clinic-1",
            specialty="general_practice",
        )
        self.assertTrue(any("patient_id" in e for e in errors))

    def test_missing_doctor_id_returns_error(self) -> None:
        errors = validate_consultation_creation(
            patient_id="pat-1",
            doctor_id="",
            clinic_id="clinic-1",
            specialty="general_practice",
        )
        self.assertTrue(any("doctor_id" in e for e in errors))

    def test_missing_clinic_id_returns_error(self) -> None:
        errors = validate_consultation_creation(
            patient_id="pat-1",
            doctor_id="doc-1",
            clinic_id="",
            specialty="general_practice",
        )
        self.assertTrue(any("clinic_id" in e for e in errors))

    def test_missing_specialty_returns_error(self) -> None:
        errors = validate_consultation_creation(
            patient_id="pat-1",
            doctor_id="doc-1",
            clinic_id="clinic-1",
            specialty="",
        )
        self.assertTrue(any("specialty" in e for e in errors))

    def test_multiple_missing_fields_returns_multiple_errors(self) -> None:
        errors = validate_consultation_creation(
            patient_id="",
            doctor_id="",
            clinic_id="",
            specialty="",
        )
        self.assertEqual(len(errors), 4)


class CanFinalizeTest(unittest.TestCase):
    """Test can_finalize rule."""

    def test_under_physician_review_returns_true(self) -> None:
        c = _make_consultation_with_status(ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.assertTrue(can_finalize(c))

    def test_started_returns_false(self) -> None:
        c = _make_consultation_with_status(ConsultationStatus.STARTED)
        self.assertFalse(can_finalize(c))

    def test_recording_returns_false(self) -> None:
        c = _make_consultation_with_status(ConsultationStatus.RECORDING)
        self.assertFalse(can_finalize(c))

    def test_in_processing_returns_false(self) -> None:
        c = _make_consultation_with_status(ConsultationStatus.IN_PROCESSING)
        self.assertFalse(can_finalize(c))

    def test_processing_failed_returns_false(self) -> None:
        c = _make_consultation_with_status(ConsultationStatus.PROCESSING_FAILED)
        self.assertFalse(can_finalize(c))

    def test_draft_generated_returns_false(self) -> None:
        c = _make_consultation_with_status(ConsultationStatus.DRAFT_GENERATED)
        self.assertFalse(can_finalize(c))

    def test_finalized_returns_false(self) -> None:
        c = _make_consultation_with_status(ConsultationStatus.FINALIZED)
        self.assertFalse(can_finalize(c))


if __name__ == "__main__":
    unittest.main()
