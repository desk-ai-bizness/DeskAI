"""Unit tests for the log_context() utility."""

import unittest

from deskai.shared.logging import log_context


class LogContextTest(unittest.TestCase):
    """Verify that log_context() builds safe structured-log dicts."""

    # --- Basic behaviour ---

    def test_returns_empty_dict_for_no_args(self) -> None:
        self.assertEqual(log_context(), {})

    def test_passes_through_non_none_values(self) -> None:
        result = log_context(consultation_id="c-1", doctor_id="d-1")
        self.assertEqual(
            result,
            {"consultation_id": "c-1", "doctor_id": "d-1"},
        )

    def test_filters_out_none_values(self) -> None:
        result = log_context(
            consultation_id="c-1",
            patient_id=None,
        )
        self.assertEqual(result, {"consultation_id": "c-1"})
        self.assertNotIn("patient_id", result)

    def test_returns_empty_dict_when_all_values_none(self) -> None:
        self.assertEqual(
            log_context(a=None, b=None, c=None),
            {},
        )

    # --- Type preservation ---

    def test_preserves_string_values(self) -> None:
        result = log_context(event="consultation_created")
        self.assertEqual(result["event"], "consultation_created")

    def test_preserves_integer_values(self) -> None:
        result = log_context(duration_ms=42, http_status=200)
        self.assertEqual(result["duration_ms"], 42)
        self.assertEqual(result["http_status"], 200)

    def test_preserves_boolean_values(self) -> None:
        result = log_context(found=True, active=False)
        self.assertIs(result["found"], True)
        self.assertIs(result["active"], False)

    def test_preserves_float_values(self) -> None:
        result = log_context(ratio=0.95)
        self.assertAlmostEqual(result["ratio"], 0.95)

    # --- Falsy-but-valid values are NOT filtered ---

    def test_keeps_zero(self) -> None:
        result = log_context(count=0)
        self.assertIn("count", result)
        self.assertEqual(result["count"], 0)

    def test_keeps_empty_string(self) -> None:
        result = log_context(path="")
        self.assertIn("path", result)
        self.assertEqual(result["path"], "")

    def test_keeps_false(self) -> None:
        result = log_context(exists=False)
        self.assertIn("exists", result)
        self.assertIs(result["exists"], False)

    def test_keeps_empty_list(self) -> None:
        result = log_context(items=[])
        self.assertIn("items", result)
        self.assertEqual(result["items"], [])

    # --- Mixed scenarios ---

    def test_mixed_none_and_valid_values(self) -> None:
        result = log_context(
            clinic_id="cl-1",
            doctor_id=None,
            http_status=200,
            request_id=None,
            found=True,
        )
        self.assertEqual(
            result,
            {"clinic_id": "cl-1", "http_status": 200, "found": True},
        )

    def test_single_kwarg_none_returns_empty(self) -> None:
        self.assertEqual(log_context(x=None), {})

    def test_single_kwarg_non_none_returns_single_entry(self) -> None:
        self.assertEqual(log_context(x="hello"), {"x": "hello"})


if __name__ == "__main__":
    unittest.main()
