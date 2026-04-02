"""Unit tests for the consultation HTTP handlers."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
)
from tests.conftest import (
    make_apigw_event,
    make_sample_consultation,
    make_sample_doctor_profile,
)


class HandleCreateConsultationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_handle_create_consultation_success(self) -> None:
        from deskai.handlers.http.consultation_handler import (
            handle_create_consultation,
        )

        consultation = make_sample_consultation()
        self.container.create_consultation.execute.return_value = consultation

        event = make_apigw_event(
            path="/v1/consultations",
            method="POST",
            body={
                "patient_id": "pat-001",
                "specialty": "general_practice",
                "scheduled_date": "2026-04-01",
                "notes": "First visit",
            },
        )
        resp = handle_create_consultation(event, self.container)

        self.assertEqual(resp["statusCode"], 201)
        body = json.loads(resp["body"])
        self.assertEqual(body["consultation_id"], "cons-001")
        self.assertEqual(body["status"], "started")

    def test_handle_create_consultation_missing_fields(self) -> None:
        from deskai.handlers.http.consultation_handler import (
            handle_create_consultation,
        )

        event = make_apigw_event(
            path="/v1/consultations",
            method="POST",
            body={"notes": "only notes"},
        )
        resp = handle_create_consultation(event, self.container)

        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "validation_error")


class HandleListConsultationsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_handle_list_consultations_success(self) -> None:
        from deskai.handlers.http.consultation_handler import (
            handle_list_consultations,
        )

        consultations = [
            make_sample_consultation(consultation_id="c1"),
            make_sample_consultation(consultation_id="c2"),
        ]
        self.container.list_consultations.execute.return_value = consultations

        event = make_apigw_event(
            path="/v1/consultations",
            method="GET",
            query_string_parameters={"from": "2026-04-01", "to": "2026-04-30"},
        )
        resp = handle_list_consultations(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["total_count"], 2)
        self.assertEqual(len(body["consultations"]), 2)


class HandleGetConsultationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_handle_get_consultation_success(self) -> None:
        from deskai.handlers.http.consultation_handler import (
            handle_get_consultation,
        )

        consultation = make_sample_consultation()
        self.container.get_consultation.execute.return_value = consultation

        event = make_apigw_event(
            path="/v1/consultations/cons-001",
            method="GET",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_get_consultation(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["consultation_id"], "cons-001")
        self.assertIn("session", body)
        self.assertIn("processing", body)

    def test_handle_get_consultation_not_found(self) -> None:
        from deskai.handlers.http.consultation_handler import (
            handle_get_consultation,
        )

        self.container.get_consultation.execute.side_effect = (
            ConsultationNotFoundError("Not found")
        )

        event = make_apigw_event(
            path="/v1/consultations/cons-missing",
            method="GET",
            path_parameters={"id": "cons-missing"},
        )
        resp = handle_get_consultation(event, self.container)

        self.assertEqual(resp["statusCode"], 404)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "not_found")

    def test_handle_get_consultation_ownership_error(self) -> None:
        from deskai.handlers.http.consultation_handler import (
            handle_get_consultation,
        )

        consultation = make_sample_consultation(doctor_id="other-doc")
        self.container.get_consultation.execute.return_value = consultation

        event = make_apigw_event(
            path="/v1/consultations/cons-001",
            method="GET",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_get_consultation(event, self.container)

        self.assertEqual(resp["statusCode"], 403)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "forbidden")

    def test_handle_get_consultation_missing_id(self) -> None:
        from deskai.handlers.http.consultation_handler import (
            handle_get_consultation,
        )

        event = make_apigw_event(
            path="/v1/consultations/",
            method="GET",
        )
        resp = handle_get_consultation(event, self.container)

        self.assertEqual(resp["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
