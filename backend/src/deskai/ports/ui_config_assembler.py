"""Port interface for UI configuration assembly."""

from abc import ABC, abstractmethod

from deskai.domain.auth.value_objects import PlanType


class UiConfigAssembler(ABC):
    """Contract for building the UI config payload."""

    @abstractmethod
    def assemble(self, plan_type: PlanType) -> dict:
        """Build the complete UI config payload for the given plan type."""
