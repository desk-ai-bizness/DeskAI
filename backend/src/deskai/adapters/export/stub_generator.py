"""Stub adapter for ExportGenerator -- raises NotImplementedError."""

from deskai.ports.export_generator import ExportGenerator


class StubExportGenerator(ExportGenerator):
    """Placeholder until a real export generator is built."""

    def generate_pdf(self, consultation_data: dict) -> bytes:
        raise NotImplementedError(
            "Not yet implemented: ExportGenerator.generate_pdf"
        )
