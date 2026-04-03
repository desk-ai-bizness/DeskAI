"""Port interface for consultation export generation."""

from abc import ABC, abstractmethod


class ExportGenerator(ABC):
    """Contract for generating consultation exports."""

    @abstractmethod
    def generate_pdf(self, consultation_data: dict) -> bytes:
        """Generate a PDF export from finalized consultation data."""
