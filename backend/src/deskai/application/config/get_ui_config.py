"""Use case for retrieving the backend-driven UI configuration."""

from deskai.bff.ui_config.assembler import assemble_ui_config
from deskai.domain.auth.value_objects import AuthContext


class GetUiConfigUseCase:
    """Return the assembled UI config for the authenticated user's plan."""

    def execute(self, auth_context: AuthContext) -> dict:
        return assemble_ui_config(auth_context.plan_type)
