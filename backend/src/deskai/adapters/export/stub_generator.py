"""Stub adapter for ExportGenerator -- raises NotImplementedError."""

from deskai.domain.consultation.entities import Consultation
from deskai.domain.export.value_objects import ExportFormat, ExportResult
from deskai.ports.export_generator import ExportGenerator


class StubExportGenerator(ExportGenerator):
    """Placeholder until a real export generator is built."""

    def generate(
        self, consultation: Consultation, fmt: ExportFormat
    ) -> ExportResult:
        raise NotImplementedError(
            "Not yet implemented: ExportGenerator.generate"
        )
