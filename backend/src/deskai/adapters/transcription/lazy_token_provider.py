"""Lazy-initializing wrapper for TranscriptionTokenProvider.

Defers secret loading and provider construction until the first
token method is actually called.  This prevents cold-start failures
from blocking unrelated endpoints (auth, patients, etc.) when the
provider secret is temporarily inaccessible.
"""

from collections.abc import Callable
from typing import Any

from deskai.ports.transcription_token_provider import TranscriptionTokenProvider
from deskai.shared.logging import get_logger

logger = get_logger()


class LazyTranscriptionTokenProvider(TranscriptionTokenProvider):
    """Wraps a factory that produces the real TranscriptionTokenProvider.

    The factory is invoked on the first method call, not at init time.
    If the factory raises, the error propagates to the caller and the
    next call will retry (the failed result is not cached).
    """

    def __init__(self, factory: Callable[[], TranscriptionTokenProvider]) -> None:
        self._factory = factory
        self._delegate: TranscriptionTokenProvider | None = None

    def _get_delegate(self) -> TranscriptionTokenProvider:
        if self._delegate is None:
            logger.info("lazy_token_provider_initializing")
            self._delegate = self._factory()
            logger.info("lazy_token_provider_ready")
        return self._delegate

    def create_single_use_token(self, scope: str = "realtime_scribe") -> dict[str, Any]:
        return self._get_delegate().create_single_use_token(scope)
