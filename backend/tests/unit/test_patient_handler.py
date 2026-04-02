"""Unit tests for the patient HTTP handlers."""

import json
import unittest
from unittest.mock import MagicMock

from tests.conftest import (
    make_apigw_event,
    make_sample_doctor_profile,
    make_sample_patient,
)


class HandleCreatePatientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_handle_create_patient_success(self) -> None:
        from deskai.handlers.http.patient_handler import (
            handle_create_patient,
        )

        patient = make_sample_patient()
        self.container.create_patient.execute.return_value = patient

        event = make_apigw_event(
            path="/v1/patients",
            method="POST",
            body={
                "name": "Joao Silva",
                "date_of_birth": "1990-05-15",
            },
        )
        resp = handle_create_patient(event, self.container)

        self.assertEqual(resp["statusCode"], 201)
        body = json.loads(resp["body"])
        self.assertEqual(body["patient_id"], "pat-001")
        self.assertEqual(body["name"], "Joao Silva")

    def test_handle_create_patient_missing_fields(self) -> None:
        from deskai.handlers.http.patient_handler import (
            handle_create_patient,
        )

        event = make_apigw_event(
            path="/v1/patients",
            method="POST",
            body={"name": "Joao"},
        )
        resp = handle_create_patient(event, self.container)

        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "validation_error")


class HandleListPatientsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_handle_list_patients_success(self) -> None:
        from deskai.handlers.http.patient_handler import (
            handle_list_patients,
        )

        patients = [
            make_sample_patient(patient_id="p1"),
            make_sample_patient(patient_id="p2"),
        ]
        self.container.list_patients.execute.return_value = patients

        event = make_apigw_event(
            path="/v1/patients",
            method="GET",
            query_string_parameters={"search": "Silva"},
        )
        resp = handle_list_patients(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(len(body["patients"]), 2)


if __name__ == "__main__":
    unittest.main()
