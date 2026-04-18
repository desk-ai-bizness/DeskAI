"""Tests for screen config -- dead code removal verification."""

import inspect
import unittest

from deskai.bff.ui_config import screen_config


class TestScreenConfig(unittest.TestCase):
    def test_get_review_screen_config_exists(self):
        self.assertTrue(hasattr(screen_config, "get_review_screen_config"))

    def test_dead_code_removed(self):
        members = dict(inspect.getmembers(screen_config))
        self.assertNotIn("get_consultation_list_config", members)

    def test_review_screen_has_required_sections(self):
        config = screen_config.get_review_screen_config()
        self.assertIn("section_order", config)
        self.assertIn("sections", config)
        expected = {"transcript", "medical_history", "summary", "insights"}
        self.assertEqual(set(config["section_order"]), expected)

    def test_review_section_titles_use_pt_br_accents(self):
        config = screen_config.get_review_screen_config()
        sections = config["sections"]
        self.assertEqual(sections["transcript"]["title"], "Transcrição")
        self.assertEqual(sections["medical_history"]["title"], "História Clínica")
