"""Port interface for UI config assembly."""

from abc import ABC, abstractmethod

from deskai.domain.auth.value_objects import PlanType


class UiConfigAssembler(ABC):
    """Contract for assembling the backend-driven UI configuration."""

    @abstractmethod
    def assemble(self, plan_type: PlanType) -> dict:
        """Build the complete UI config payload for the given plan type."""
