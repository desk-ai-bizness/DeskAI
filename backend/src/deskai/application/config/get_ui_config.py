"""Use case for retrieving the backend-driven UI configuration."""

from deskai.domain.auth.value_objects import AuthContext
from deskai.ports.ui_config_assembler import UiConfigAssembler


class GetUiConfigUseCase:
    """Return the assembled UI config for the authenticated user's plan."""

    def __init__(self, ui_config_assembler: UiConfigAssembler) -> None:
        self._assembler = ui_config_assembler

    def execute(self, auth_context: AuthContext) -> dict:
        return self._assembler.assemble(auth_context.plan_type)
