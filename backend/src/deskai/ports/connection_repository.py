"""Connection repository port interface."""

from abc import ABC, abstractmethod

from deskai.domain.session.value_objects import ConnectionInfo


class ConnectionRepository(ABC):
    """Abstract repository for WebSocket connection metadata."""

    @abstractmethod
    def save(self, connection: ConnectionInfo) -> None: ...

    @abstractmethod
    def find_by_connection_id(self, connection_id: str) -> ConnectionInfo | None: ...

    @abstractmethod
    def remove(self, connection_id: str) -> None: ...
