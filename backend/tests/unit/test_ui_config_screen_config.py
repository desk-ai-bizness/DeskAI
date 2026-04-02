"""Unit tests for BFF UI config screen configuration module."""

import unittest

from deskai.bff.ui_config.screen_config import (
    get_consultation_list_config,
    get_review_screen_config,
)

EXPECTED_SECTION_ORDER = [
    "transcript",
    "medical_history",
    "summary",
    "insights",
]


class GetReviewScreenConfigTest(unittest.TestCase):
    def test_returns_section_order_and_sections(self) -> None:
        config = get_review_screen_config()
        self.assertIn("section_order", config)
        self.assertIn("sections", config)

    def test_section_order_matches_expected(self) -> None:
        config = get_review_screen_config()
        self.assertEqual(
            config["section_order"], EXPECTED_SECTION_ORDER
        )

    def test_sections_has_all_required_keys(self) -> None:
        config = get_review_screen_config()
        sections = config["sections"]
        for name in EXPECTED_SECTION_ORDER:
            with self.subTest(section=name):
                self.assertIn(name, sections)

    def test_each_section_has_title_editable_visible(self) -> None:
        config = get_review_screen_config()
        sections = config["sections"]
        for name in EXPECTED_SECTION_ORDER:
            with self.subTest(section=name):
                section = sections[name]
                self.assertIsInstance(section["title"], str)
                self.assertIsInstance(section["editable"], bool)
                self.assertIsInstance(section["visible"], bool)

    def test_transcript_is_visible_but_not_editable(self) -> None:
        config = get_review_screen_config()
        transcript = config["sections"]["transcript"]
        self.assertTrue(transcript["visible"])
        self.assertFalse(transcript["editable"])

    def test_medical_history_is_editable(self) -> None:
        config = get_review_screen_config()
        section = config["sections"]["medical_history"]
        self.assertTrue(section["editable"])
        self.assertTrue(section["visible"])

    def test_summary_is_editable(self) -> None:
        config = get_review_screen_config()
        section = config["sections"]["summary"]
        self.assertTrue(section["editable"])
        self.assertTrue(section["visible"])

    def test_insights_is_visible_but_not_editable(self) -> None:
        config = get_review_screen_config()
        section = config["sections"]["insights"]
        self.assertTrue(section["visible"])
        self.assertFalse(section["editable"])


class GetConsultationListConfigTest(unittest.TestCase):
    def test_returns_page_size(self) -> None:
        config = get_consultation_list_config()
        self.assertEqual(config["page_size"], 20)

    def test_returns_default_sort(self) -> None:
        config = get_consultation_list_config()
        self.assertEqual(
            config["default_sort"], "created_at_desc"
        )

    def test_returns_default_status_filter(self) -> None:
        config = get_consultation_list_config()
        self.assertEqual(config["default_status_filter"], "all")


if __name__ == "__main__":
    unittest.main()
