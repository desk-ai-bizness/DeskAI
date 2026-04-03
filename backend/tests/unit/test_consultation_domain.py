"""Unit tests for the consultation domain."""

import unittest
from dataclasses import FrozenInstanceError

from deskai.domain.consultation.entities import (
    Consultation,
    ConsultationStatus,
)
from deskai.shared.errors import DomainValidationError


class ConsultationStatusTest(unittest.TestCase):
    def test_all_seven_status_values_exist(self) -> None:
        expected = {
            "started",
            "recording",
            "in_processing",
            "processing_failed",
            "draft_generated",
            "under_physician_review",
            "finalized",
        }
        actual = {s.value for s in ConsultationStatus}
        self.assertEqual(actual, expected)

    def test_status_count(self) -> None:
        self.assertEqual(len(ConsultationStatus), 7)


class ConsultationEntityTest(unittest.TestCase):
    def test_create_consultation_with_defaults(self) -> None:
        c = Consultation(
            consultation_id="c-001",
            clinic_id="clinic-1",
            doctor_id="doc-1",
            patient_id="pat-1",
            specialty="general",
        )
        self.assertEqual(c.consultation_id, "c-001")
        self.assertEqual(c.clinic_id, "clinic-1")
        self.assertEqual(c.doctor_id, "doc-1")
        self.assertEqual(c.patient_id, "pat-1")
        self.assertEqual(c.specialty, "general")
        self.assertEqual(c.status, ConsultationStatus.STARTED)

    def test_create_consultation_with_explicit_status(self) -> None:
        c = Consultation(
            consultation_id="c-002",
            clinic_id="clinic-1",
            doctor_id="doc-1",
            patient_id="pat-1",
            specialty="general",
            status=ConsultationStatus.FINALIZED,
        )
        self.assertEqual(c.status, ConsultationStatus.FINALIZED)

    def test_consultation_is_frozen_dataclass(self) -> None:
        """Consultation is a frozen dataclass — attribute assignment raises."""
        c = Consultation(
            consultation_id="c-003",
            clinic_id="clinic-1",
            doctor_id="doc-1",
            patient_id="pat-1",
            specialty="general",
        )
        with self.assertRaises(FrozenInstanceError):
            c.status = ConsultationStatus.RECORDING  # type: ignore[misc]

    def test_empty_consultation_id_raises(self) -> None:
        with self.assertRaises(DomainValidationError):
            Consultation(
                consultation_id="",
                clinic_id="clinic-1",
                doctor_id="doc-1",
                patient_id="pat-1",
                specialty="general",
            )


if __name__ == "__main__":
    unittest.main()
