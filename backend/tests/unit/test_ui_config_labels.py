"""Unit tests for BFF UI config labels module."""

import unittest

from deskai.bff.ui_config.labels import (
    get_insight_categories,
    get_labels,
    get_status_labels,
)
from deskai.domain.consultation.entities import ConsultationStatus

REQUIRED_LABEL_KEYS = frozenset(
    {
        "consultation_list_title",
        "new_consultation_button",
        "start_recording_button",
        "stop_recording_button",
        "review_title",
        "finalize_button",
        "export_button",
        "ai_disclaimer",
        "completeness_warning",
        "live_session_header",
    }
)

ALL_STATUSES = frozenset(s.value for s in ConsultationStatus)

INSIGHT_CATEGORY_KEYS = frozenset(
    {
        "documentation_gap",
        "consistency_issue",
        "clinical_attention",
    }
)


class GetLabelsTest(unittest.TestCase):
    def test_returns_all_required_keys(self) -> None:
        labels = get_labels()
        self.assertEqual(set(labels.keys()), REQUIRED_LABEL_KEYS)

    def test_all_values_are_non_empty_strings(self) -> None:
        labels = get_labels()
        for key, value in labels.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, str)
                self.assertTrue(
                    len(value) > 0,
                    f"Label '{key}' must not be empty",
                )

    def test_visible_labels_use_pt_br_accents(self) -> None:
        labels = get_labels()
        self.assertEqual(labels["start_recording_button"], "Iniciar Gravação")
        self.assertEqual(labels["stop_recording_button"], "Parar Gravação")
        self.assertEqual(labels["review_title"], "Revisão da Consulta")
        self.assertEqual(
            labels["ai_disclaimer"],
            "Conteúdo gerado por IA — sujeito a revisão médica.",
        )
        self.assertEqual(labels["live_session_header"], "Sessão ao Vivo")


class GetStatusLabelsTest(unittest.TestCase):
    def test_returns_labels_for_all_statuses(self) -> None:
        status_labels = get_status_labels()
        self.assertEqual(set(status_labels.keys()), ALL_STATUSES)

    def test_all_status_labels_are_non_empty_strings(self) -> None:
        status_labels = get_status_labels()
        for key, value in status_labels.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, str)
                self.assertTrue(
                    len(value) > 0,
                    f"Status label '{key}' must not be empty",
                )

    def test_status_labels_use_pt_br_accents(self) -> None:
        status_labels = get_status_labels()
        self.assertEqual(
            status_labels[ConsultationStatus.UNDER_PHYSICIAN_REVIEW.value],
            "Em Revisão Médica",
        )


class GetInsightCategoriesTest(unittest.TestCase):
    def test_returns_all_three_categories(self) -> None:
        categories = get_insight_categories()
        self.assertEqual(
            set(categories.keys()), INSIGHT_CATEGORY_KEYS
        )

    def test_each_category_has_required_shape(self) -> None:
        categories = get_insight_categories()
        for name, cat in categories.items():
            with self.subTest(category=name):
                self.assertIn("label", cat)
                self.assertIn("icon", cat)
                self.assertIn("severity", cat)
                self.assertIsInstance(cat["label"], str)
                self.assertIsInstance(cat["icon"], str)
                self.assertIsInstance(cat["severity"], str)

    def test_icon_values_are_valid(self) -> None:
        valid_icons = {"info", "warning", "alert"}
        categories = get_insight_categories()
        for name, cat in categories.items():
            with self.subTest(category=name):
                self.assertIn(cat["icon"], valid_icons)

    def test_severity_values_are_valid(self) -> None:
        valid_severities = {"low", "medium", "high"}
        categories = get_insight_categories()
        for name, cat in categories.items():
            with self.subTest(category=name):
                self.assertIn(cat["severity"], valid_severities)

    def test_category_labels_use_pt_br_accents(self) -> None:
        categories = get_insight_categories()
        self.assertEqual(categories["documentation_gap"]["label"], "Lacuna de Documentação")
        self.assertEqual(categories["consistency_issue"]["label"], "Problema de Consistência")
        self.assertEqual(categories["clinical_attention"]["label"], "Atenção Clínica")


if __name__ == "__main__":
    unittest.main()
