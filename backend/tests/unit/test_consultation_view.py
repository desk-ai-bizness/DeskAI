"""Unit tests for the consultation BFF view builders."""

import unittest

from deskai.domain.consultation.entities import ConsultationStatus
from tests.conftest import make_sample_consultation, make_sample_patient


class BuildConsultationViewTest(unittest.TestCase):
    def test_build_consultation_view(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_view,
        )

        consultation = make_sample_consultation()
        view = build_consultation_view(consultation)

        self.assertEqual(view["consultation_id"], "cons-001")
        self.assertEqual(view["patient"], {"patient_id": "pat-001", "name": ""})
        self.assertNotIn("patient_id", view)
        self.assertEqual(view["doctor_id"], "doc-001")
        self.assertEqual(view["clinic_id"], "clinic-001")
        self.assertEqual(view["specialty"], "general_practice")
        self.assertEqual(view["status"], "started")
        self.assertEqual(view["scheduled_date"], "2026-04-01")

    def test_build_consultation_view_with_patient_name(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_view,
        )

        consultation = make_sample_consultation()
        view = build_consultation_view(consultation, patient_name="Joao Silva")

        self.assertEqual(view["patient"], {"patient_id": "pat-001", "name": "Joao Silva"})

    def test_build_consultation_list_view(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_list_view,
        )

        consultations = [
            make_sample_consultation(consultation_id="c1"),
            make_sample_consultation(consultation_id="c2"),
        ]
        view = build_consultation_list_view(consultations)

        self.assertEqual(view["total_count"], 2)
        self.assertEqual(len(view["consultations"]), 2)
        self.assertEqual(view["consultations"][0]["consultation_id"], "c1")
        self.assertEqual(view["page"], 1)
        self.assertEqual(view["page_size"], 20)

    def test_build_consultation_list_view_custom_pagination(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_list_view,
        )

        consultations = [make_sample_consultation(consultation_id="c1")]
        view = build_consultation_list_view(consultations, page=3, page_size=10)

        self.assertEqual(view["page"], 3)
        self.assertEqual(view["page_size"], 10)

    def test_build_consultation_detail_view(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            session_started_at="2026-04-01T10:30:00+00:00",
            session_ended_at="2026-04-01T11:00:00+00:00",
            processing_started_at="2026-04-01T11:01:00+00:00",
            processing_completed_at="2026-04-01T11:05:00+00:00",
            finalized_at="2026-04-01T12:00:00+00:00",
            finalized_by="doc-001",
        )
        view = build_consultation_detail_view(consultation)

        self.assertEqual(view["consultation_id"], "cons-001")
        self.assertIn("session", view)
        self.assertIsNone(view["session"]["session_id"])
        self.assertEqual(
            view["session"]["started_at"], "2026-04-01T10:30:00+00:00"
        )
        self.assertEqual(
            view["session"]["ended_at"], "2026-04-01T11:00:00+00:00"
        )
        self.assertIn("processing", view)
        self.assertEqual(
            view["processing"]["started_at"], "2026-04-01T11:01:00+00:00"
        )
        self.assertEqual(view["finalized_at"], "2026-04-01T12:00:00+00:00")
        self.assertEqual(view["finalized_by"], "doc-001")
        # STARTED status should not have a draft
        self.assertFalse(view["has_draft"])

    def test_detail_view_has_draft_true_when_draft_generated(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            status=ConsultationStatus.DRAFT_GENERATED,
        )
        view = build_consultation_detail_view(consultation)
        self.assertTrue(view["has_draft"])

    def test_detail_view_has_draft_true_when_finalized(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            status=ConsultationStatus.FINALIZED,
        )
        view = build_consultation_detail_view(consultation)
        self.assertTrue(view["has_draft"])

    def test_detail_view_has_draft_false_when_recording(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            status=ConsultationStatus.RECORDING,
        )
        view = build_consultation_detail_view(consultation)
        self.assertFalse(view["has_draft"])

    def test_build_patient_view(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_patient_view,
        )

        patient = make_sample_patient()
        view = build_patient_view(patient)

        self.assertEqual(view["patient_id"], "pat-001")
        self.assertEqual(view["name"], "Joao Silva")
        self.assertEqual(view["date_of_birth"], "1990-05-15")
        self.assertEqual(view["clinic_id"], "clinic-001")


    def test_detail_view_includes_actions(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            status=ConsultationStatus.STARTED,
        )
        view = build_consultation_detail_view(consultation)

        self.assertIn("actions", view)
        self.assertIsInstance(view["actions"], dict)
        self.assertTrue(view["actions"]["can_start_recording"])

    def test_detail_view_includes_warnings(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            status=ConsultationStatus.STARTED,
        )
        view = build_consultation_detail_view(consultation)

        self.assertIn("warnings", view)
        self.assertIsInstance(view["warnings"], list)

    def test_detail_view_processing_failed_warning(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            status=ConsultationStatus.PROCESSING_FAILED,
            error_details={"reason": "timeout"},
        )
        view = build_consultation_detail_view(consultation)

        self.assertEqual(len(view["warnings"]), 1)
        self.assertEqual(
            view["warnings"][0]["type"], "processing_failed"
        )

    def test_detail_view_started_no_warnings(self) -> None:
        from deskai.bff.views.consultation_view import (
            build_consultation_detail_view,
        )

        consultation = make_sample_consultation(
            status=ConsultationStatus.STARTED,
        )
        view = build_consultation_detail_view(consultation)

        self.assertEqual(view["warnings"], [])


if __name__ == "__main__":
    unittest.main()
