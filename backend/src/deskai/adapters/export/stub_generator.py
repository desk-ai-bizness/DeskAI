"""Stub adapter for ExportGenerator."""

from deskai.ports.export_generator import ExportGenerator


class StubExportGenerator(ExportGenerator):
    def generate_pdf(self, consultation_data: dict) -> bytes:
        raise NotImplementedError("Not yet implemented: ExportGenerator.generate_pdf")
