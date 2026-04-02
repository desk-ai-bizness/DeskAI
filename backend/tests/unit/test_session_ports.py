"""Unit tests for session port interfaces (ABCs)."""

import inspect
from abc import ABC

from deskai.ports.session_repository import SessionRepository
from deskai.ports.connection_repository import ConnectionRepository


# ---------------------------------------------------------------------------
# SessionRepository port
# ---------------------------------------------------------------------------


class TestSessionRepository:
    def test_is_abstract_base_class(self):
        assert issubclass(SessionRepository, ABC)

    def test_has_save_method(self):
        assert hasattr(SessionRepository, "save")
        assert inspect.isabstract(SessionRepository)

    def test_has_find_by_id_method(self):
        sig = inspect.signature(SessionRepository.find_by_id)
        params = list(sig.parameters.keys())
        assert "session_id" in params

    def test_has_find_active_by_consultation_id_method(self):
        sig = inspect.signature(SessionRepository.find_active_by_consultation_id)
        params = list(sig.parameters.keys())
        assert "consultation_id" in params

    def test_has_update_method(self):
        assert hasattr(SessionRepository, "update")

    def test_has_delete_method(self):
        sig = inspect.signature(SessionRepository.delete)
        params = list(sig.parameters.keys())
        assert "session_id" in params

    def test_cannot_instantiate_directly(self):
        try:
            SessionRepository()
            assert False, "Should not be instantiable"
        except TypeError:
            pass


# ---------------------------------------------------------------------------
# ConnectionRepository port
# ---------------------------------------------------------------------------


class TestConnectionRepository:
    def test_is_abstract_base_class(self):
        assert issubclass(ConnectionRepository, ABC)

    def test_has_save_method(self):
        assert hasattr(ConnectionRepository, "save")

    def test_has_find_by_connection_id_method(self):
        sig = inspect.signature(ConnectionRepository.find_by_connection_id)
        params = list(sig.parameters.keys())
        assert "connection_id" in params

    def test_has_remove_method(self):
        sig = inspect.signature(ConnectionRepository.remove)
        params = list(sig.parameters.keys())
        assert "connection_id" in params

    def test_cannot_instantiate_directly(self):
        try:
            ConnectionRepository()
            assert False, "Should not be instantiable"
        except TypeError:
            pass
