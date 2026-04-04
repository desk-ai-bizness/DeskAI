"""Review domain value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewUpdate:
    """Value object representing a physician's review update request."""

    medical_history: dict | None = None
    summary: dict | None = None
    insight_actions: list[dict] | None = None

    def has_changes(self) -> bool:
        """Return True if any field was provided."""
        return any(
            [
                self.medical_history is not None,
                self.summary is not None,
                self.insight_actions is not None,
            ]
        )

    def edited_fields(self) -> list[str]:
        """Return list of field names that were edited."""
        fields = []
        if self.medical_history is not None:
            fields.append("medical_history")
        if self.summary is not None:
            fields.append("summary")
        if self.insight_actions is not None:
            fields.append("insights")
        return fields
