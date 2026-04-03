"""Tests for the feature flag evaluator."""

from deskai.bff.feature_flags.evaluator import evaluate_flags
from deskai.domain.auth.value_objects import PlanType


class TestEvaluateFlags:
    def test_free_trial_flags_are_disabled(self):
        result = evaluate_flags(PlanType.FREE_TRIAL)
        assert result["export_pdf_enabled"] is False
        assert result["insights_enabled"] is False
        assert result["audio_playback_enabled"] is False

    def test_plus_flags_enable_export_and_insights(self):
        result = evaluate_flags(PlanType.PLUS)
        assert result["export_pdf_enabled"] is True
        assert result["insights_enabled"] is True
        assert result["audio_playback_enabled"] is False

    def test_pro_flags_enable_everything(self):
        result = evaluate_flags(PlanType.PRO)
        assert result["export_pdf_enabled"] is True
        assert result["insights_enabled"] is True
        assert result["audio_playback_enabled"] is True

    def test_returns_plan_limits(self):
        result = evaluate_flags(PlanType.FREE_TRIAL)
        assert "consultation_monthly_limit" in result
        assert "consultation_max_duration_minutes" in result
        assert "audio_retention_days" in result

    def test_returns_trial_duration(self):
        result = evaluate_flags(PlanType.FREE_TRIAL)
        assert "trial_duration_days" in result
        assert isinstance(result["trial_duration_days"], int)

    def test_all_plans_return_same_keys(self):
        keys = None
        for plan in PlanType:
            result = evaluate_flags(plan)
            if keys is None:
                keys = set(result.keys())
            else:
                assert set(result.keys()) == keys
