"""Unit tests for the patient HTTP handlers."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.entities import ConsultationStatus
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
                "cpf": "529.982.247-25",
            },
        )
        resp = handle_create_patient(event, self.container)

        self.assertEqual(resp["statusCode"], 201)
        body = json.loads(resp["body"])
        self.assertEqual(body["patient_id"], "pat-001")
        self.assertEqual(body["name"], "Joao Silva")
        self.assertEqual(body["cpf"], "529.***.***-25")
        self.assertIn("date_of_birth", body)

    def test_handle_create_patient_empty_name_returns_400(self) -> None:
        from deskai.handlers.http.patient_handler import (
            handle_create_patient,
        )

        event = make_apigw_event(
            path="/v1/patients",
            method="POST",
            body={
                "name": "",
                "cpf": "529.982.247-25",
                "date_of_birth": "1990-05-15",
            },
        )
        resp = handle_create_patient(event, self.container)

        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "validation_error")

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

    def test_handle_create_patient_passes_cpf_and_optional_dob_to_use_case(self) -> None:
        from deskai.handlers.http.patient_handler import (
            handle_create_patient,
        )

        patient = make_sample_patient(date_of_birth=None)
        self.container.create_patient.execute.return_value = patient

        event = make_apigw_event(
            path="/v1/patients",
            method="POST",
            body={
                "name": "Joao Silva",
                "cpf": "529.982.247-25",
            },
        )
        handle_create_patient(event, self.container)

        _, kwargs = self.container.create_patient.execute.call_args
        self.assertEqual(kwargs["name"], "Joao Silva")
        self.assertEqual(kwargs["cpf"], "529.982.247-25")
        self.assertIsNone(kwargs["date_of_birth"])


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
        self.assertEqual(body["patients"][0]["cpf"], "529.***.***-25")


    def test_handle_list_patients_empty_list_returns_200(self) -> None:
        from deskai.handlers.http.patient_handler import (
            handle_list_patients,
        )

        self.container.list_patients.execute.return_value = []

        event = make_apigw_event(
            path="/v1/patients",
            method="GET",
            query_string_parameters={"search": "Nonexistent"},
        )
        resp = handle_list_patients(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(len(body["patients"]), 0)


class HandleGetPatientDetailTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_handle_get_patient_detail_success(self) -> None:
        from deskai.application.patient.get_patient_detail import (
            PatientDetailResult,
            PatientHistoryItem,
        )
        from deskai.handlers.http.patient_handler import (
            handle_get_patient,
        )
        from tests.conftest import make_sample_consultation

        patient = make_sample_patient()
        consultation = make_sample_consultation(
            consultation_id="cons-1",
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-02T10:00:00+00:00",
        )
        self.container.get_patient_detail.execute.return_value = PatientDetailResult(
            patient=patient,
            history=[
                PatientHistoryItem(
                    consultation=consultation,
                    preview={"summary": "Paciente retornou para revisao."},
                )
            ],
        )

        event = make_apigw_event(
            path="/v1/patients/pat-001",
            method="GET",
            path_parameters={"id": "pat-001"},
        )
        resp = handle_get_patient(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["patient"]["cpf"], "529.***.***-25")
        self.assertEqual(body["history"][0]["consultation_id"], "cons-1")
        self.assertEqual(
            body["history"][0]["preview"]["summary"],
            "Paciente retornou para revisao.",
        )


if __name__ == "__main__":
    unittest.main()
