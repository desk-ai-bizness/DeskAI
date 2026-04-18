"""Contract tests for the patient HTTP OpenAPI schemas."""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import Any

import yaml

from deskai.domain.consultation.entities import ConsultationStatus
from tests.conftest import make_sample_consultation, make_sample_patient

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / "contracts" / "http" / "patients.yaml"
)


def _load_patient_contract() -> dict[str, Any]:
    with _CONTRACT_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _schema(name: str) -> dict[str, Any]:
    return _load_patient_contract()["components"]["schemas"][name]


def _resolve_ref(ref: str) -> dict[str, Any]:
    prefix = "#/components/schemas/"
    if not ref.startswith(prefix):
        raise AssertionError(f"Unsupported contract ref in test: {ref}")
    return _schema(ref.removeprefix(prefix))


def _validate(schema: dict[str, Any], value: Any) -> None:
    if "$ref" in schema:
        return _validate(_resolve_ref(schema["$ref"]), value)

    if "anyOf" in schema:
        failures: list[AssertionError] = []
        for option in schema["anyOf"]:
            try:
                _validate(option, value)
                return
            except AssertionError as exc:
                failures.append(exc)
        raise AssertionError(f"{value!r} did not match any schema option: {failures}")

    expected_type = schema.get("type")
    if expected_type == "null":
        assert value is None
        return
    if expected_type == "object":
        assert isinstance(value, dict), f"Expected object, got {type(value).__name__}"
        required = set(schema.get("required", []))
        missing = required - set(value)
        assert not missing, f"Missing required fields: {sorted(missing)}"
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}))
            extras = set(value) - allowed
            assert not extras, f"Unexpected fields: {sorted(extras)}"
        for key, child_schema in schema.get("properties", {}).items():
            if key in value:
                _validate(child_schema, value[key])
        return
    if expected_type == "array":
        assert isinstance(value, list), f"Expected array, got {type(value).__name__}"
        item_schema = schema.get("items", {})
        for item in value:
            _validate(item_schema, item)
        return
    if expected_type == "string":
        assert isinstance(value, str), f"Expected string, got {type(value).__name__}"
        if "enum" in schema:
            assert value in schema["enum"], f"{value!r} not in {schema['enum']}"
        if "pattern" in schema:
            assert re.fullmatch(schema["pattern"], value), (
                f"{value!r} does not match {schema['pattern']}"
            )
        return
    if expected_type == "integer":
        assert isinstance(value, int), f"Expected integer, got {type(value).__name__}"
        return
    if expected_type == "boolean":
        assert isinstance(value, bool), f"Expected boolean, got {type(value).__name__}"
        return


class PatientHttpContractTest(unittest.TestCase):
    def test_post_patients_declares_duplicate_cpf_conflict_response(self) -> None:
        contract = _load_patient_contract()

        responses = contract["paths"]["/v1/patients"]["post"]["responses"]

        self.assertIn("409", responses)
        self.assertEqual(responses["409"]["description"], "Patient CPF already exists in clinic")
        self.assertEqual(
            responses["409"]["content"]["application/json"]["schema"]["$ref"],
            "errors.yaml#/components/schemas/ErrorResponse",
        )

    def test_create_patient_request_schema_requires_name_and_cpf_only(self) -> None:
        payload = {
            "name": "Joao Silva",
            "cpf": "529.982.247-25",
        }

        _validate(_schema("CreatePatientRequest"), payload)

    def test_patient_view_schema_matches_bff_response_shape(self) -> None:
        from deskai.bff.views.consultation_view import build_patient_view

        patient = make_sample_patient(
            patient_id="11111111-1111-4111-8111-111111111111",
            clinic_id="22222222-2222-4222-8222-222222222222",
            date_of_birth=None,
        )

        _validate(_schema("PatientView"), build_patient_view(patient))

    def test_patient_list_view_schema_matches_bff_response_shape(self) -> None:
        from deskai.bff.views.consultation_view import build_patient_view

        patient = make_sample_patient(
            patient_id="11111111-1111-4111-8111-111111111111",
            clinic_id="22222222-2222-4222-8222-222222222222",
        )

        _validate(_schema("PatientListView"), {"patients": [build_patient_view(patient)]})

    def test_patient_detail_view_schema_matches_bff_response_shape(self) -> None:
        from deskai.application.patient.get_patient_detail import (
            PatientDetailResult,
            PatientHistoryItem,
        )
        from deskai.bff.views.consultation_view import build_patient_detail_view

        patient = make_sample_patient(
            patient_id="11111111-1111-4111-8111-111111111111",
            clinic_id="22222222-2222-4222-8222-222222222222",
        )
        consultation = make_sample_consultation(
            consultation_id="33333333-3333-4333-8333-333333333333",
            patient_id=patient.patient_id,
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-18T12:00:00+00:00",
        )
        result = PatientDetailResult(
            patient=patient,
            history=[
                PatientHistoryItem(
                    consultation=consultation,
                    preview={"summary": "Resumo revisado."},
                )
            ],
        )

        _validate(_schema("PatientDetailView"), build_patient_detail_view(result))


if __name__ == "__main__":
    unittest.main()
