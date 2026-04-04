"""Stub adapter for ExportGenerator -- raises NotImplementedError."""

from typing import Any

from deskai.domain.export.value_objects import ExportFormat, ExportResult
from deskai.ports.export_generator import ExportGenerator


class StubExportGenerator(ExportGenerator):
    """Placeholder until a real export generator is built."""

    def generate(
        self,
        consultation_id: str,
        fmt: ExportFormat,
        metadata: dict[str, Any],
        medical_history: dict[str, Any],
        summary: dict[str, Any],
        accepted_insights: list[dict[str, Any]],
    ) -> ExportResult:
        raise NotImplementedError("Not yet implemented: ExportGenerator.generate")
