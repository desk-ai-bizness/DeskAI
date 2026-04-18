"""Unit tests for patient detail BFF views."""

import unittest

from deskai.domain.consultation.entities import ConsultationStatus
from tests.conftest import make_sample_consultation, make_sample_patient


class PatientDetailViewTest(unittest.TestCase):
    def test_build_patient_detail_view_masks_cpf_and_includes_history(self) -> None:
        from deskai.application.patient.get_patient_detail import (
            PatientDetailResult,
            PatientHistoryItem,
        )
        from deskai.bff.views.consultation_view import build_patient_detail_view

        patient = make_sample_patient(date_of_birth=None)
        consultation = make_sample_consultation(
            consultation_id="cons-001",
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-02T12:00:00+00:00",
        )

        view = build_patient_detail_view(
            PatientDetailResult(
                patient=patient,
                history=[
                    PatientHistoryItem(
                        consultation=consultation,
                        preview={"summary": "Resumo revisado."},
                    )
                ],
            )
        )

        self.assertEqual(view["patient"]["cpf"], "529.***.***-25")
        self.assertIsNone(view["patient"]["date_of_birth"])
        self.assertEqual(view["history"][0]["consultation_id"], "cons-001")
        self.assertEqual(view["history"][0]["status"], "finalized")
        self.assertEqual(view["history"][0]["finalized_at"], "2026-04-02T12:00:00+00:00")
        self.assertEqual(view["history"][0]["preview"], {"summary": "Resumo revisado."})


if __name__ == "__main__":
    unittest.main()
