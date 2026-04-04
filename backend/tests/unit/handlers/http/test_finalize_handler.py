"""Unit tests for the finalize HTTP handler."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.consultation.entities import ConsultationStatus
from tests.conftest import (
    make_apigw_event,
    make_sample_consultation,
    make_sample_doctor_profile,
)


class HandleFinalizeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_finalize_returns_200_with_finalize_view(self) -> None:
        from deskai.handlers.http.finalize_handler import handle_finalize

        consultation = make_sample_consultation(
            status=ConsultationStatus.FINALIZED,
            finalized_at="2026-04-01T14:00:00+00:00",
            finalized_by="doc-001",
        )
        self.container.finalize_consultation.execute.return_value = consultation

        event = make_apigw_event(
            path="/v1/consultations/cons-001/finalize",
            method="POST",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_finalize(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["consultation_id"], "cons-001")
        self.assertEqual(body["status"], "finalized")
        self.assertEqual(body["finalized_at"], "2026-04-01T14:00:00+00:00")
        self.assertEqual(body["finalized_by"], "doc-001")

    def test_finalize_returns_400_without_consultation_id(self) -> None:
        from deskai.handlers.http.finalize_handler import handle_finalize

        event = make_apigw_event(
            path="/v1/consultations//finalize",
            method="POST",
            path_parameters={},
        )
        resp = handle_finalize(event, self.container)

        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "validation_error")


if __name__ == "__main__":
    unittest.main()
