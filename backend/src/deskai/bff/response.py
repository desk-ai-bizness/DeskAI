"""Shared BFF response shape helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BffResponse:
    """Standardized BFF payload envelope."""

    data: dict[str, object]
    contract_version: str
