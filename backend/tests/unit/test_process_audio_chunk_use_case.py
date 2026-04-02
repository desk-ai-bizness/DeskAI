"""Unit tests for the ProcessAudioChunk use case."""

import unittest
from unittest.mock import MagicMock, patch

from deskai.domain.session.entities import Session, SessionState
from deskai.domain.session.exceptions import (
    AudioChunkRejectedError,
    SessionOwnershipError,
)

_MOD = "deskai.application.transcription.process_audio_chunk"


def _make_session(state=SessionState.RECORDING, chunks=5, **overrides):
    defaults = dict(
        session_id="sess-001",
        consultation_id="cons-001",
        doctor_id="doc-001",
        clinic_id="clinic-001",
        state=state,
        started_at="2026-04-02T10:00:00+00:00",
        audio_chunks_received=chunks,
    )
    defaults.update(overrides)
    return Session(**defaults)


class ProcessAudioChunkUseCaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.session_repo = MagicMock()
        self.transcription_provider = MagicMock()

        from deskai.application.transcription.process_audio_chunk import (
            ProcessAudioChunkUseCase,
        )

        self.use_case = ProcessAudioChunkUseCase(
            session_repo=self.session_repo,
            transcription_provider=self.transcription_provider,
        )

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_forwards_audio_to_provider(self, _mock_time: MagicMock) -> None:
        session = _make_session(state=SessionState.RECORDING, chunks=5)
        self.session_repo.find_by_id.return_value = session

        self.use_case.execute(
            session_id="sess-001",
            doctor_id="doc-001",
            audio_data=b"fake-audio-bytes",
        )

        self.transcription_provider.send_audio_chunk.assert_called_once_with(
            "sess-001", b"fake-audio-bytes"
        )

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_increments_audio_chunks_received(self, _mock_time: MagicMock) -> None:
        session = _make_session(state=SessionState.RECORDING, chunks=5)
        self.session_repo.find_by_id.return_value = session

        self.use_case.execute(
            session_id="sess-001",
            doctor_id="doc-001",
            audio_data=b"audio",
        )

        self.session_repo.update.assert_called_once()
        updated = self.session_repo.update.call_args[0][0]
        self.assertEqual(updated.audio_chunks_received, 6)

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_updates_last_activity_at(self, _mock_time: MagicMock) -> None:
        session = _make_session(state=SessionState.RECORDING, chunks=0)
        self.session_repo.find_by_id.return_value = session

        self.use_case.execute(
            session_id="sess-001",
            doctor_id="doc-001",
            audio_data=b"audio",
        )

        updated = self.session_repo.update.call_args[0][0]
        self.assertEqual(updated.last_activity_at, "2026-04-02T12:00:00+00:00")

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_returns_none(self, _mock_time: MagicMock) -> None:
        session = _make_session(state=SessionState.RECORDING)
        self.session_repo.find_by_id.return_value = session

        result = self.use_case.execute(
            session_id="sess-001",
            doctor_id="doc-001",
            audio_data=b"audio",
        )

        self.assertIsNone(result)

    def test_rejects_when_session_not_recording(self) -> None:
        session = _make_session(state=SessionState.ENDED)
        self.session_repo.find_by_id.return_value = session

        with self.assertRaises(AudioChunkRejectedError):
            self.use_case.execute(
                session_id="sess-001",
                doctor_id="doc-001",
                audio_data=b"audio",
            )

        self.transcription_provider.send_audio_chunk.assert_not_called()

    def test_rejects_when_wrong_doctor(self) -> None:
        session = _make_session(state=SessionState.RECORDING, doctor_id="doc-other")
        self.session_repo.find_by_id.return_value = session

        with self.assertRaises(SessionOwnershipError):
            self.use_case.execute(
                session_id="sess-001",
                doctor_id="doc-001",
                audio_data=b"audio",
            )

        self.transcription_provider.send_audio_chunk.assert_not_called()

    @patch(f"{_MOD}.utc_now_iso", return_value="2026-04-02T12:00:00+00:00")
    def test_accepts_active_state(self, _mock_time: MagicMock) -> None:
        session = _make_session(state=SessionState.ACTIVE, chunks=0)
        self.session_repo.find_by_id.return_value = session

        self.use_case.execute(
            session_id="sess-001",
            doctor_id="doc-001",
            audio_data=b"audio",
        )

        self.transcription_provider.send_audio_chunk.assert_called_once()
        self.session_repo.update.assert_called_once()

    def test_session_not_found_raises(self) -> None:
        from deskai.domain.session.exceptions import SessionNotFoundError

        self.session_repo.find_by_id.return_value = None

        with self.assertRaises(SessionNotFoundError):
            self.use_case.execute(
                session_id="sess-missing",
                doctor_id="doc-001",
                audio_data=b"audio",
            )


if __name__ == "__main__":
    unittest.main()
