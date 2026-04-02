"""Unit tests for transcription domain exceptions."""

import unittest

from deskai.domain.transcription.exceptions import (
    NormalizationError,
    ProviderSessionError,
    ProviderUnavailableError,
    TranscriptionError,
    TranscriptionIncompleteError,
)
from deskai.shared.errors import DeskAIError


class TranscriptionExceptionsHierarchyTest(unittest.TestCase):
    def test_all_exceptions_extend_deskai_error(self) -> None:
        exceptions = [
            TranscriptionError,
            ProviderSessionError,
            TranscriptionIncompleteError,
            NormalizationError,
            ProviderUnavailableError,
        ]
        for exc_cls in exceptions:
            with self.subTest(exc=exc_cls.__name__):
                self.assertTrue(issubclass(exc_cls, DeskAIError))

    def test_transcription_error_is_base(self) -> None:
        self.assertTrue(issubclass(TranscriptionError, DeskAIError))

    def test_provider_session_error_extends_transcription_error(self) -> None:
        self.assertTrue(
            issubclass(ProviderSessionError, TranscriptionError)
        )

    def test_transcription_incomplete_error_extends_transcription_error(
        self,
    ) -> None:
        self.assertTrue(
            issubclass(TranscriptionIncompleteError, TranscriptionError)
        )

    def test_normalization_error_extends_transcription_error(self) -> None:
        self.assertTrue(
            issubclass(NormalizationError, TranscriptionError)
        )

    def test_provider_unavailable_error_extends_transcription_error(
        self,
    ) -> None:
        self.assertTrue(
            issubclass(ProviderUnavailableError, TranscriptionError)
        )


class TranscriptionExceptionsMessagesTest(unittest.TestCase):
    def test_transcription_error_message(self) -> None:
        exc = TranscriptionError("generic transcription failure")
        self.assertEqual(str(exc), "generic transcription failure")

    def test_provider_session_error_message(self) -> None:
        exc = ProviderSessionError("session timed out")
        self.assertEqual(str(exc), "session timed out")

    def test_normalization_error_message(self) -> None:
        exc = NormalizationError("missing speaker field")
        self.assertEqual(str(exc), "missing speaker field")

    def test_provider_unavailable_error_message(self) -> None:
        exc = ProviderUnavailableError("ElevenLabs API down")
        self.assertEqual(str(exc), "ElevenLabs API down")

    def test_transcription_incomplete_error_message(self) -> None:
        exc = TranscriptionIncompleteError("only 40% transcribed")
        self.assertEqual(str(exc), "only 40% transcribed")


if __name__ == "__main__":
    unittest.main()
