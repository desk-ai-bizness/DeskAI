"""Unit tests for review HTTP handlers."""

import json
import unittest
from unittest.mock import MagicMock

from deskai.domain.review.entities import ReviewPayload
from tests.conftest import make_apigw_event, make_sample_doctor_profile


class HandleGetReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_get_review_returns_200_with_review_view(self) -> None:
        from deskai.handlers.http.review_handler import handle_get_review

        payload = ReviewPayload(
            consultation_id="cons-001",
            medical_history={"queixa_principal": {"descricao": "Headache"}},
            summary={"subjetivo": {"queixa_principal": "Headache"}},
            insights=[],
        )
        self.container.open_review.execute.return_value = payload

        event = make_apigw_event(
            path="/v1/consultations/cons-001/review",
            method="GET",
            path_parameters={"id": "cons-001"},
        )
        resp = handle_get_review(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["consultation_id"], "cons-001")
        self.assertIn("medical_history", body)
        self.assertIn("summary", body)
        self.assertIn("insights", body)

    def test_get_review_returns_400_without_consultation_id(self) -> None:
        from deskai.handlers.http.review_handler import handle_get_review

        event = make_apigw_event(
            path="/v1/consultations//review",
            method="GET",
            path_parameters={},
        )
        resp = handle_get_review(event, self.container)

        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertEqual(body["error"]["code"], "validation_error")


class HandleUpdateReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = MagicMock()
        self.profile = make_sample_doctor_profile()
        self.container.get_current_user.execute.return_value = self.profile

    def test_update_review_returns_200_with_updated_view(self) -> None:
        from deskai.handlers.http.review_handler import handle_update_review

        payload = ReviewPayload(
            consultation_id="cons-001",
            medical_history={"queixa_principal": {"descricao": "Edited"}},
            summary={"subjetivo": {"queixa_principal": "Headache"}},
            insights=[],
            medical_history_edited=True,
        )
        self.container.update_review.execute.return_value = {}
        self.container.open_review.execute.return_value = payload

        event = make_apigw_event(
            path="/v1/consultations/cons-001/review",
            method="PUT",
            path_parameters={"id": "cons-001"},
            body={"medical_history": {"queixa_principal": {"descricao": "Edited"}}},
        )
        resp = handle_update_review(event, self.container)

        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["consultation_id"], "cons-001")
        self.assertTrue(body["medical_history"]["edited_by_physician"])

    def test_update_review_passes_edits_to_use_case(self) -> None:
        from deskai.handlers.http.review_handler import handle_update_review

        payload = ReviewPayload(
            consultation_id="cons-001",
            medical_history={},
            summary={},
            insights=[],
        )
        self.container.update_review.execute.return_value = {}
        self.container.open_review.execute.return_value = payload

        event = make_apigw_event(
            path="/v1/consultations/cons-001/review",
            method="PUT",
            path_parameters={"id": "cons-001"},
            body={
                "medical_history": {"edited": True},
                "summary": {"edited": True},
                "insights": [{"insight_id": "0", "action": "accepted"}],
            },
        )
        handle_update_review(event, self.container)

        self.container.update_review.execute.assert_called_once()
        call_kwargs = self.container.update_review.execute.call_args
        update = call_kwargs.kwargs.get("update") or call_kwargs[1].get("update")
        self.assertEqual(update.medical_history, {"edited": True})
        self.assertEqual(update.summary, {"edited": True})
        self.assertEqual(
            update.insight_actions,
            [{"insight_id": "0", "action": "accepted"}],
        )


if __name__ == "__main__":
    unittest.main()
