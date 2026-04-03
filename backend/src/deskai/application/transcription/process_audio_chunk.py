"""Process an audio chunk during a real-time session."""

from dataclasses import dataclass, replace

from deskai.domain.session.exceptions import SessionNotFoundError
from deskai.domain.session.services import SessionService
from deskai.ports.session_repository import SessionRepository
from deskai.ports.transcription_provider import TranscriptionProvider
from deskai.shared.time import utc_now_iso


@dataclass(frozen=True)
class ProcessAudioChunkUseCase:
    """Validate session, forward audio to provider, update chunk count."""

    session_repo: SessionRepository
    transcription_provider: TranscriptionProvider

    def execute(
        self,
        session_id: str,
        doctor_id: str,
        audio_data: bytes,
    ) -> None:
        session = self.session_repo.find_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session {session_id} not found")

        SessionService.validate_audio_chunk(
            session_state=session.state,
            session_doctor_id=session.doctor_id,
            requesting_doctor_id=doctor_id,
        )

        self.transcription_provider.send_audio_chunk(session_id, audio_data)

        session = replace(
            session,
            audio_chunks_received=session.audio_chunks_received + 1,
            last_activity_at=utc_now_iso(),
        )
        self.session_repo.update(session)
