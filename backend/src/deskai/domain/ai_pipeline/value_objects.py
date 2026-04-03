"""AI pipeline domain value objects."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StructuredOutput:
    """Immutable result of a structured LLM generation task."""

    task: str
    payload: dict[str, Any]
