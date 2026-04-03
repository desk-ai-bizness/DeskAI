"""Tests for plan-dependent feature flag definitions and evaluation."""

from deskai.bff.feature_flags.evaluator import evaluate_flags
from deskai.bff.feature_flags.flags import PLAN_FEATURE_FLAGS
from deskai.domain.auth.value_objects import PlanType

# ---------------------------------------------------------------------------
# Data-level checks (from main) — validate the PLAN_FEATURE_FLAGS dict
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Runtime checks (from branch) — verify evaluate_flags() returns correct
# values at runtime, not just that the static dict is correct.
# ---------------------------------------------------------------------------


class TestEvaluateFlags:
    def test_free_trial_export_disabled(self):
        assert evaluate_flags(PlanType.FREE_TRIAL)["export_pdf_enabled"] is False

    def test_free_trial_insights_disabled(self):
        assert evaluate_flags(PlanType.FREE_TRIAL)["insights_enabled"] is False

    def test_plus_export_enabled(self):
        assert evaluate_flags(PlanType.PLUS)["export_pdf_enabled"] is True

    def test_pro_audio_playback_enabled(self):
        assert evaluate_flags(PlanType.PRO)["audio_playback_enabled"] is True
