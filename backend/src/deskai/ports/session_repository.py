"""Session repository port interface."""

from abc import ABC, abstractmethod

from deskai.domain.session.entities import Session


class SessionRepository(ABC):
    """Abstract repository for session persistence."""

    @abstractmethod
    def save(self, session: Session) -> None: ...

    @abstractmethod
    def find_by_id(self, session_id: str) -> Session | None: ...

    @abstractmethod
    def find_active_by_consultation_id(self, consultation_id: str) -> Session | None: ...

    @abstractmethod
    def update(self, session: Session) -> None: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...
