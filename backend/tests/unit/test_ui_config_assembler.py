"""Unit tests for BFF UI config assembler module."""

import unittest

from deskai.bff.ui_config.assembler import assemble_ui_config
from deskai.domain.auth.value_objects import PlanType

REQUIRED_TOP_LEVEL_KEYS = frozenset(
    {
        "version",
        "locale",
        "labels",
        "review_screen",
        "insight_categories",
        "status_labels",
        "feature_flags",
    }
)


class AssembleUiConfigTest(unittest.TestCase):
    def test_returns_all_required_top_level_keys(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        self.assertEqual(
            set(config.keys()), REQUIRED_TOP_LEVEL_KEYS
        )

    def test_version_is_one_dot_zero(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        self.assertEqual(config["version"], "1.0")

    def test_locale_is_pt_br(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        self.assertEqual(config["locale"], "pt-BR")

    def test_labels_is_dict_with_string_values(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        labels = config["labels"]
        self.assertIsInstance(labels, dict)
        for key, value in labels.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, str)

    def test_review_screen_has_section_order(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        self.assertIn(
            "section_order", config["review_screen"]
        )

    def test_insight_categories_has_three_entries(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        self.assertEqual(len(config["insight_categories"]), 3)

    def test_status_labels_has_seven_entries(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        self.assertEqual(len(config["status_labels"]), 7)

    def test_feature_flags_contains_required_keys(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        flags = config["feature_flags"]
        self.assertIn("export_enabled", flags)
        self.assertIn("insights_enabled", flags)
        self.assertIn("audio_playback_enabled", flags)

    def test_feature_flags_values_are_booleans(self) -> None:
        config = assemble_ui_config(PlanType.PLUS)
        flags = config["feature_flags"]
        for key in (
            "export_enabled",
            "insights_enabled",
            "audio_playback_enabled",
        ):
            with self.subTest(key=key):
                self.assertIsInstance(flags[key], bool)

    def test_works_for_all_plan_types(self) -> None:
        for plan_type in PlanType:
            with self.subTest(plan=plan_type.value):
                config = assemble_ui_config(plan_type)
                self.assertEqual(
                    set(config.keys()),
                    REQUIRED_TOP_LEVEL_KEYS,
                )


if __name__ == "__main__":
    unittest.main()
