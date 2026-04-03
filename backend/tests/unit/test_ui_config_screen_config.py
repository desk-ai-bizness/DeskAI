"""Tests for screen config -- dead code removal verification."""

import inspect

from deskai.bff.ui_config import screen_config


class TestScreenConfig:
    def test_get_review_screen_config_exists(self):
        assert hasattr(screen_config, "get_review_screen_config")

    def test_dead_code_removed(self):
        members = dict(inspect.getmembers(screen_config))
        assert "get_consultation_list_config" not in members

    def test_review_screen_has_required_sections(self):
        config = screen_config.get_review_screen_config()
        assert "section_order" in config
        assert "sections" in config
        expected = {"transcript", "medical_history", "summary", "insights"}
        assert set(config["section_order"]) == expected
