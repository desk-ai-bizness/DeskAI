"""Unit tests for BFF UI config screen configuration module."""

import unittest
from deskai.bff.ui_config.screen_config import get_review_screen_config

class GetReviewScreenConfigTest(unittest.TestCase):
    def test_has_section_order(self):
        c = get_review_screen_config()
        self.assertIn("section_order", c)
        self.assertIn("sections", c)

    def test_order(self):
        c = get_review_screen_config()
        self.assertEqual(c["section_order"], ["transcript", "medical_history", "summary", "insights"])

    def test_transcript_not_editable(self):
        self.assertFalse(get_review_screen_config()["sections"]["transcript"]["editable"])

if __name__ == "__main__":
    unittest.main()
