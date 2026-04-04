"""Port interface for consultation export generation."""

from abc import ABC, abstractmethod
from typing import Any

from deskai.domain.export.value_objects import ExportFormat, ExportResult


class ExportGenerator(ABC):
    """Contract for generating exportable consultation documents."""

    @abstractmethod
    def generate(
        self,
        consultation_id: str,
        fmt: ExportFormat,
        metadata: dict[str, Any],
        medical_history: dict[str, Any],
        summary: dict[str, Any],
        accepted_insights: list[dict[str, Any]],
    ) -> ExportResult:
        """Produce an export artifact from finalized consultation content."""
