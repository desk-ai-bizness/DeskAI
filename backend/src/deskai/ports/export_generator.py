"""Port interface for consultation export generation."""

from abc import ABC, abstractmethod

from deskai.domain.consultation.entities import Consultation
from deskai.domain.export.value_objects import ExportFormat, ExportResult


class ExportGenerator(ABC):
    """Contract for generating exportable consultation documents."""

    @abstractmethod
    def generate(
        self, consultation: Consultation, fmt: ExportFormat
    ) -> ExportResult:
        """Produce an export artifact for the given consultation."""
