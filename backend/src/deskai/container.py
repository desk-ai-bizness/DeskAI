"""Dependency wiring entrypoint for backend handlers."""

from dataclasses import dataclass

from deskai.shared.config import Settings, load_settings


@dataclass(frozen=True)
class Container:
    """Resolved runtime dependencies for handler execution."""

    settings: Settings


def build_container() -> Container:
    """Create the dependency container.

    Task 003 provides only bootstrap wiring. Concrete adapters and use cases
    are added by implementation tasks.
    """

    return Container(settings=load_settings())
