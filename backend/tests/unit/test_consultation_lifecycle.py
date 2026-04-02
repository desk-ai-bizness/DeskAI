"""Unit tests for consultation lifecycle — status transitions."""

import unittest

from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.consultation.exceptions import InvalidStatusTransitionError
from deskai.domain.consultation.services import (
    ALLOWED_TRANSITIONS,
    transition_consultation,
    validate_transition,
)


def _make_consultation(
    status: ConsultationStatus = ConsultationStatus.STARTED,
) -> Consultation:
    return Consultation(
        consultation_id="c-100",
        clinic_id="clinic-1",
        doctor_id="doc-1",
        patient_id="pat-1",
        specialty="general_practice",
        status=status,
    )


class ValidateTransitionTest(unittest.TestCase):
    """Test the pure validate_transition function."""

    def test_started_to_recording(self) -> None:
        self.assertTrue(validate_transition(ConsultationStatus.STARTED, ConsultationStatus.RECORDING))

    def test_recording_to_in_processing(self) -> None:
        self.assertTrue(validate_transition(ConsultationStatus.RECORDING, ConsultationStatus.IN_PROCESSING))

    def test_in_processing_to_draft_generated(self) -> None:
        self.assertTrue(validate_transition(ConsultationStatus.IN_PROCESSING, ConsultationStatus.DRAFT_GENERATED))

    def test_in_processing_to_processing_failed(self) -> None:
        self.assertTrue(validate_transition(ConsultationStatus.IN_PROCESSING, ConsultationStatus.PROCESSING_FAILED))

    def test_processing_failed_to_in_processing(self) -> None:
        self.assertTrue(validate_transition(ConsultationStatus.PROCESSING_FAILED, ConsultationStatus.IN_PROCESSING))

    def test_draft_generated_to_under_physician_review(self) -> None:
        self.assertTrue(
            validate_transition(ConsultationStatus.DRAFT_GENERATED, ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        )

    def test_under_physician_review_to_finalized(self) -> None:
        self.assertTrue(
            validate_transition(ConsultationStatus.UNDER_PHYSICIAN_REVIEW, ConsultationStatus.FINALIZED)
        )

    def test_under_physician_review_to_itself_is_allowed(self) -> None:
        """Physician edits keep the same status — this must be allowed."""
        self.assertTrue(
            validate_transition(
                ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
                ConsultationStatus.UNDER_PHYSICIAN_REVIEW,
            )
        )


class ForbiddenTransitionsTest(unittest.TestCase):
    """Verify that invalid transitions are rejected."""

    def test_started_to_finalized_is_forbidden(self) -> None:
        self.assertFalse(validate_transition(ConsultationStatus.STARTED, ConsultationStatus.FINALIZED))

    def test_started_to_in_processing_is_forbidden(self) -> None:
        self.assertFalse(validate_transition(ConsultationStatus.STARTED, ConsultationStatus.IN_PROCESSING))

    def test_recording_to_finalized_is_forbidden(self) -> None:
        self.assertFalse(validate_transition(ConsultationStatus.RECORDING, ConsultationStatus.FINALIZED))

    def test_finalized_to_started_is_forbidden(self) -> None:
        self.assertFalse(validate_transition(ConsultationStatus.FINALIZED, ConsultationStatus.STARTED))

    def test_finalized_to_recording_is_forbidden(self) -> None:
        self.assertFalse(validate_transition(ConsultationStatus.FINALIZED, ConsultationStatus.RECORDING))

    def test_finalized_to_in_processing_is_forbidden(self) -> None:
        self.assertFalse(validate_transition(ConsultationStatus.FINALIZED, ConsultationStatus.IN_PROCESSING))

    def test_finalized_to_under_physician_review_is_forbidden(self) -> None:
        self.assertFalse(
            validate_transition(ConsultationStatus.FINALIZED, ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        )

    def test_draft_generated_to_recording_is_forbidden(self) -> None:
        self.assertFalse(validate_transition(ConsultationStatus.DRAFT_GENERATED, ConsultationStatus.RECORDING))

    def test_finalized_is_terminal(self) -> None:
        """No transitions out of FINALIZED."""
        allowed = ALLOWED_TRANSITIONS[ConsultationStatus.FINALIZED]
        self.assertEqual(allowed, set())


class TransitionConsultationTest(unittest.TestCase):
    """Test the transition_consultation function that mutates state."""

    def test_successful_transition_updates_status(self) -> None:
        c = _make_consultation(ConsultationStatus.STARTED)
        result = transition_consultation(c, ConsultationStatus.RECORDING)
        self.assertEqual(result.status, ConsultationStatus.RECORDING)

    def test_transition_sets_updated_at(self) -> None:
        c = _make_consultation(ConsultationStatus.STARTED)
        self.assertEqual(c.updated_at, "")
        transition_consultation(c, ConsultationStatus.RECORDING)
        self.assertNotEqual(c.updated_at, "")

    def test_invalid_transition_raises_error(self) -> None:
        c = _make_consultation(ConsultationStatus.STARTED)
        with self.assertRaises(InvalidStatusTransitionError):
            transition_consultation(c, ConsultationStatus.FINALIZED)

    def test_transition_to_finalized_sets_finalized_fields(self) -> None:
        c = _make_consultation(ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        transition_consultation(
            c,
            ConsultationStatus.FINALIZED,
            finalized_at="2026-04-01T12:00:00+00:00",
            finalized_by="doc-1",
        )
        self.assertEqual(c.status, ConsultationStatus.FINALIZED)
        self.assertEqual(c.finalized_at, "2026-04-01T12:00:00+00:00")
        self.assertEqual(c.finalized_by, "doc-1")

    def test_transition_to_processing_failed_sets_error_details(self) -> None:
        c = _make_consultation(ConsultationStatus.IN_PROCESSING)
        error_info = {"reason": "timeout", "step": "transcription"}
        transition_consultation(
            c,
            ConsultationStatus.PROCESSING_FAILED,
            error_details=error_info,
        )
        self.assertEqual(c.status, ConsultationStatus.PROCESSING_FAILED)
        self.assertEqual(c.error_details, error_info)

    def test_transition_returns_same_consultation_object(self) -> None:
        c = _make_consultation(ConsultationStatus.STARTED)
        result = transition_consultation(c, ConsultationStatus.RECORDING)
        self.assertIs(result, c)

    def test_under_physician_review_to_itself_is_idempotent(self) -> None:
        c = _make_consultation(ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        transition_consultation(c, ConsultationStatus.UNDER_PHYSICIAN_REVIEW)
        self.assertEqual(c.status, ConsultationStatus.UNDER_PHYSICIAN_REVIEW)

    def test_invalid_transition_error_message_contains_statuses(self) -> None:
        c = _make_consultation(ConsultationStatus.STARTED)
        with self.assertRaises(InvalidStatusTransitionError) as ctx:
            transition_consultation(c, ConsultationStatus.FINALIZED)
        msg = str(ctx.exception)
        self.assertIn("started", msg)
        self.assertIn("finalized", msg)


if __name__ == "__main__":
    unittest.main()
