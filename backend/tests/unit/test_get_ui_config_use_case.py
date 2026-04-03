"""Tests for GetUiConfigUseCase -- verifies layer violation is fixed."""

from unittest.mock import MagicMock

from deskai.application.config.get_ui_config import GetUiConfigUseCase
from deskai.domain.auth.value_objects import AuthContext, PlanType
from deskai.ports.ui_config_assembler import UiConfigAssembler


class TestGetUiConfigUseCase:
    def test_delegates_to_assembler_port(self):
        mock_assembler = MagicMock(spec=UiConfigAssembler)
        mock_assembler.assemble.return_value = {"version": "1.0"}

        use_case = GetUiConfigUseCase(ui_config_assembler=mock_assembler)
        auth_context = AuthContext(
            doctor_id="doc-123",
            email="doc@clinic.com",
            clinic_id="clinic-1",
            plan_type=PlanType.PLUS,
        )

        result = use_case.execute(auth_context)

        mock_assembler.assemble.assert_called_once_with(PlanType.PLUS)
        assert result == {"version": "1.0"}

    def test_passes_plan_type_from_auth_context(self):
        mock_assembler = MagicMock(spec=UiConfigAssembler)
        mock_assembler.assemble.return_value = {}

        use_case = GetUiConfigUseCase(ui_config_assembler=mock_assembler)

        for plan in PlanType:
            auth = AuthContext(
                doctor_id="d", email="d@c.com", clinic_id="c", plan_type=plan
            )
            use_case.execute(auth)
            mock_assembler.assemble.assert_called_with(plan)

    def test_does_not_import_from_bff(self):
        import inspect

        import deskai.application.config.get_ui_config as mod

        source = inspect.getsource(mod)
        assert "deskai.bff" not in source
