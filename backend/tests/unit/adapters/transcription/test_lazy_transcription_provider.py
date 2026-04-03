"""Tests for LazyTranscriptionProvider — deferred initialization wrapper."""

import unittest
from unittest.mock import MagicMock, call

from deskai.adapters.transcription.lazy_provider import (
    LazyTranscriptionProvider,
)
from deskai.ports.transcription_provider import TranscriptionProvider


def _make_mock_provider() -> TranscriptionProvider:
    """Create a mock that satisfies the TranscriptionProvider interface."""
    mock = MagicMock(spec=TranscriptionProvider)
    mock.start_realtime_session.return_value = {
        "session_id": "s1",
        "state": "ready",
    }
    mock.get_session_state.return_value = "streaming"
    mock.finish_realtime_session.return_value = {
        "session_id": "s1",
        "state": "closed",
    }
    mock.fetch_final_transcript.return_value = {"text": "hello"}
    return mock


class TestLazyProviderInitialization(unittest.TestCase):
    """Factory must NOT be called until a provider method is invoked."""

    def test_factory_not_called_on_init(self) -> None:
        factory = MagicMock(return_value=_make_mock_provider())
        LazyTranscriptionProvider(factory)
        factory.assert_not_called()

    def test_factory_called_on_first_method(self) -> None:
        factory = MagicMock(return_value=_make_mock_provider())
        lazy = LazyTranscriptionProvider(factory)
        lazy.start_realtime_session("s1", "pt")
        factory.assert_called_once()

    def test_factory_called_only_once_across_multiple_methods(self) -> None:
        factory = MagicMock(return_value=_make_mock_provider())
        lazy = LazyTranscriptionProvider(factory)
        lazy.start_realtime_session("s1", "pt")
        lazy.send_audio_chunk("s1", b"data")
        lazy.get_session_state("s1")
        factory.assert_called_once()


class TestLazyProviderDelegation(unittest.TestCase):
    """All TranscriptionProvider methods must delegate to the real provider."""

    def setUp(self) -> None:
        self.delegate = _make_mock_provider()
        self.lazy = LazyTranscriptionProvider(lambda: self.delegate)

    def test_start_realtime_session_delegates(self) -> None:
        result = self.lazy.start_realtime_session("s1", "pt")
        self.delegate.start_realtime_session.assert_called_once_with("s1", "pt")
        self.assertEqual(result, self.delegate.start_realtime_session.return_value)

    def test_send_audio_chunk_delegates(self) -> None:
        self.lazy.send_audio_chunk("s1", b"audio")
        self.delegate.send_audio_chunk.assert_called_once_with("s1", b"audio")

    def test_finish_realtime_session_delegates(self) -> None:
        result = self.lazy.finish_realtime_session("s1")
        self.delegate.finish_realtime_session.assert_called_once_with("s1")
        self.assertEqual(result, self.delegate.finish_realtime_session.return_value)

    def test_fetch_final_transcript_delegates(self) -> None:
        result = self.lazy.fetch_final_transcript("s1")
        self.delegate.fetch_final_transcript.assert_called_once_with("s1")
        self.assertEqual(result, self.delegate.fetch_final_transcript.return_value)

    def test_get_session_state_delegates(self) -> None:
        result = self.lazy.get_session_state("s1")
        self.delegate.get_session_state.assert_called_once_with("s1")
        self.assertEqual(result, self.delegate.get_session_state.return_value)


class TestLazyProviderErrorPropagation(unittest.TestCase):
    """Factory errors must propagate at call time, not init time."""

    def test_factory_exception_propagates_on_first_call(self) -> None:
        factory = MagicMock(side_effect=RuntimeError("KMS access denied"))
        lazy = LazyTranscriptionProvider(factory)
        with self.assertRaises(RuntimeError, msg="KMS access denied"):
            lazy.start_realtime_session("s1", "pt")

    def test_factory_exception_retries_on_next_call(self) -> None:
        """If factory fails, the next call should retry (not cache the error)."""
        delegate = _make_mock_provider()
        factory = MagicMock(side_effect=[RuntimeError("transient"), delegate])
        lazy = LazyTranscriptionProvider(factory)

        with self.assertRaises(RuntimeError):
            lazy.start_realtime_session("s1", "pt")

        # Second call should succeed after factory recovers
        result = lazy.start_realtime_session("s1", "pt")
        self.assertEqual(result, delegate.start_realtime_session.return_value)
        self.assertEqual(factory.call_count, 2)


class TestLazyProviderIsTranscriptionProvider(unittest.TestCase):
    """LazyTranscriptionProvider must satisfy the TranscriptionProvider contract."""

    def test_is_instance_of_transcription_provider(self) -> None:
        lazy = LazyTranscriptionProvider(lambda: _make_mock_provider())
        self.assertIsInstance(lazy, TranscriptionProvider)


if __name__ == "__main__":
    unittest.main()
