"""Port interface for application configuration."""

from abc import ABC, abstractmethod

from deskai.domain.config.value_objects import FeatureFlag


class ConfigRepository(ABC):
    """Read-only access to feature flags and config values."""

    @abstractmethod
    def get_feature_flag(self, flag_name: str) -> FeatureFlag | None:
        """Look up a single feature flag by name."""

    @abstractmethod
    def list_feature_flags(self) -> list[FeatureFlag]:
        """Return all known feature flags."""

    @abstractmethod
    def get_config_value(self, key: str) -> str | None:
        """Retrieve a plain-text configuration value, or None if absent."""
