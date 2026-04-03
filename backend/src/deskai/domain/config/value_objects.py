"""Config domain value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureFlag:
    """Immutable representation of a single feature flag."""

    name: str
    enabled: bool
    metadata: str = ""
