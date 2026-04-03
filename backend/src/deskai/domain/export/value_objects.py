"""Export domain value objects."""

from dataclasses import dataclass
from enum import StrEnum


class ExportFormat(StrEnum):
    """Supported export output formats."""

    PDF = "pdf"


@dataclass(frozen=True)
class ExportResult:
    """Immutable result of an export generation."""

    consultation_id: str
    format: ExportFormat
    data: bytes
    filename: str
