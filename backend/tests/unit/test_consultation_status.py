"""Unit tests for consultation domain bootstrap."""

import unittest

from deskai.domain.consultation.entities import ConsultationStatus


class ConsultationStatusTest(unittest.TestCase):
    """Ensure canonical status values match business rules."""

    def test_expected_status_values_exist(self) -> None:
        statuses = {item.value for item in ConsultationStatus}
        self.assertIn("started", statuses)
        self.assertIn("recording", statuses)
        self.assertIn("in_processing", statuses)
        self.assertIn("finalized", statuses)


if __name__ == "__main__":
    unittest.main()
