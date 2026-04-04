"""Unit tests for the export HTTP handler."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.export.entities import ExportArtifact
from deskai.domain.export.value_objects import ExportFormat
from tests.conftest import make_apigw_event, make_sample_doctor_profile


class HandleExportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_export_returns_200_with_export_view(self) -> None:
        from deskai.handlers.http.export_handler import handle_export

        artifact = ExportArtifact(
            consultation_id="cons-001",
            format=ExportFormat.PDF,
            storage_key="clinics/clinic-001/consultations/cons-001/exports/final.pdf",
            presigned_url="https://s3.example.com/presigned",
            expires_at="2026-04-01T16:00:00+00:00",
        )
        self.container.generate_export.execute.return_value = artifact

        event = make_apigw_event(
            path="/v1/consultations/cons-001/export",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_export(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["consultation_id"], "cons-001")
        self.assertEqual(body["export_url"], "https://s3.example.com/presigned")
        self.assertEqual(body["format"], "pdf")
        self.assertIn("expires_at", body)

    def test_export_returns_400_without_consultation_id(self) -> None:
        from deskai.handlers.http.export_handler import handle_export

        event = make_apigw_event(
            path="/v1/consultations//export",
            method="POST",
            path_parameters={},
        )
        resp = handle_export(event, self.container)

        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "validation_error")


if __name__ == "__main__":
    unittest.main()
