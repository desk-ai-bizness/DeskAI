"""Unit tests for the BFF action availability module."""

import unittest

from deskai.bff.action_availability import compute_actions, compute_warnings
from deskai.domain.consultation.entities import ConsultationStatus

EXPECTED_ACTION_KEYS = {
    "can_start_recording",
    "can_stop_recording",
    "can_retry_processing",
    "can_open_review",
    "can_edit_review",
    "can_finalize",
    "can_export",
}


class ComputeActionsTest(unittest.TestCase):
    def test_started_can_start_recording(self) -> None:
        actions = compute_actions(ConsultationStatus.STARTED)
        self.assertTrue(actions["can_start_recording"])
        for key in EXPECTED_ACTION_KEYS - {"can_start_recording"}:
            self.assertFalse(actions[key], f"{key} should be False for STARTED")

    def test_recording_can_stop_recording(self) -> None:
        actions = compute_actions(ConsultationStatus.RECORDING)
        self.assertTrue(actions["can_stop_recording"])
        for key in EXPECTED_ACTION_KEYS - {"can_stop_recording"}:
            self.assertFalse(actions[key], f"{key} should be False for RECORDING")

    def test_in_processing_all_false(self) -> None:
        actions = compute_actions(ConsultationStatus.IN_PROCESSING)
        for key in EXPECTED_ACTION_KEYS:
            self.assertFalse(actions[key], f"{key} should be False for IN_PROCESSING")

    def test_processing_failed_can_retry(self) -> None:
        actions = compute_actions(ConsultationStatus.PROCESSING_FAILED)
        self.assertTrue(actions["can_retry_processing"])
        for key in EXPECTED_ACTION_KEYS - {"can_retry_processing"}:
            self.assertFalse(actions[key], f"{key} should be False for PROCESSING_FAILED")

    def test_draft_generated_can_open_review(self) -> None:
        actions = compute_actions(ConsultationStatus.DRAFT_GENERATED)
        self.assertTrue(actions["can_open_review"])
        for key in EXPECTED_ACTION_KEYS - {"can_open_review"}:
            self.assertFalse(actions[key], f"{key} should be False for DRAFT_GENERATED")

    def test_under_review_can_edit_and_finalize(self) -> None:
        actions = compute_actions(ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.assertTrue(actions["can_edit_review"])
        self.assertTrue(actions["can_finalize"])
        for key in EXPECTED_ACTION_KEYS - {"can_edit_review", "can_finalize"}:
            self.assertFalse(
                actions[key],
                f"{key} should be False for UNDER_PHYSICIAN_REVIEW",
            )

    def test_finalized_can_export_when_enabled(self) -> None:
        actions = compute_actions(ConsultationStatus.FINALIZED, export_enabled=True)
        self.assertTrue(actions["can_export"])
        for key in EXPECTED_ACTION_KEYS - {"can_export"}:
            self.assertFalse(actions[key], f"{key} should be False for FINALIZED")

    def test_finalized_cannot_export_when_disabled(self) -> None:
        actions = compute_actions(ConsultationStatus.FINALIZED, export_enabled=False)
        for key in EXPECTED_ACTION_KEYS:
            self.assertFalse(actions[key], f"{key} should be False when export disabled")

    def test_all_plans_get_same_base_actions(self) -> None:
        """Action availability is status-driven, not plan-driven in MVP."""
        actions = compute_actions(ConsultationStatus.STARTED)
        self.assertEqual(set(actions.keys()), EXPECTED_ACTION_KEYS)

    def test_return_type_has_exactly_seven_keys(self) -> None:
        actions = compute_actions(ConsultationStatus.STARTED)
        self.assertIsInstance(actions, dict)
        self.assertEqual(len(actions), 7)
        self.assertEqual(set(actions.keys()), EXPECTED_ACTION_KEYS)
        for value in actions.values():
            self.assertIsInstance(value, bool)


class ComputeWarningsTest(unittest.TestCase):
    def test_processing_failed_adds_warning(self) -> None:
        warnings = compute_warnings(ConsultationStatus.PROCESSING_FAILED)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["type"], "processing_failed")
        self.assertIn("message", warnings[0])

    def test_processing_failed_with_error_details(self) -> None:
        error = {"reason": "timeout", "code": "TIMEOUT_001"}
        warnings = compute_warnings(
            ConsultationStatus.PROCESSING_FAILED,
            error_details=error,
        )
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["type"], "processing_failed")

    def test_started_no_warnings(self) -> None:
        warnings = compute_warnings(ConsultationStatus.STARTED)
        self.assertEqual(warnings, [])

    def test_finalized_no_warnings(self) -> None:
        warnings = compute_warnings(ConsultationStatus.FINALIZED)
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
