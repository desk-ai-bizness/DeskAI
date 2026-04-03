"""Tests for plan-dependent feature flag definitions."""

from deskai.bff.feature_flags.flags import PLAN_FEATURE_FLAGS
from deskai.domain.auth.value_objects import PlanType


class TestPlanFeatureFlags:
    def test_free_trial_has_nothing_enabled(self):
        flags = PLAN_FEATURE_FLAGS[PlanType.FREE_TRIAL]
        assert flags["export_pdf_enabled"] is False
        assert flags["insights_enabled"] is False
        assert flags["audio_playback_enabled"] is False

    def test_plus_has_export_and_insights(self):
        flags = PLAN_FEATURE_FLAGS[PlanType.PLUS]
        assert flags["export_pdf_enabled"] is True
        assert flags["insights_enabled"] is True
        assert flags["audio_playback_enabled"] is False

    def test_pro_has_everything_enabled(self):
        flags = PLAN_FEATURE_FLAGS[PlanType.PRO]
        assert flags["export_pdf_enabled"] is True
        assert flags["insights_enabled"] is True
        assert flags["audio_playback_enabled"] is True

    def test_all_plan_types_covered(self):
        for plan in PlanType:
            assert plan in PLAN_FEATURE_FLAGS

    def test_flag_keys_consistent(self):
        expected = {"export_pdf_enabled", "insights_enabled", "audio_playback_enabled"}
        for plan in PlanType:
            assert set(PLAN_FEATURE_FLAGS[plan].keys()) == expected
