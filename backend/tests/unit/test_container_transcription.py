"""Unit tests for container with transcription dependencies."""

import os
import unittest
from unittest.mock import MagicMock, patch

from deskai.application.session.pause_session import PauseSessionUseCase
from deskai.application.session.resume_session import ResumeSessionUseCase
from deskai.application.transcription.finalize_transcript import (
    FinalizeTranscriptUseCase,
)
from deskai.application.transcription.issue_transcription_token import (
    IssueTranscriptionTokenUseCase,
)
from deskai.container import build_container

_REQUIRED_ENV = {
    "DESKAI_COGNITO_USER_POOL_ID": "us-east-1_TestPool",
    "DESKAI_COGNITO_CLIENT_ID": "test-client-id",
    "DESKAI_ELEVENLABS_SECRET_NAME": "deskai/dev/elevenlabs",
    "DESKAI_ARTIFACTS_BUCKET": "deskai-dev-artifacts",
    "AWS_DEFAULT_REGION": "us-east-1",
}

_SECRET_VALUE = '{"elevenlabs_api_key": "test-key-123"}'


def _build_with_mocked_boto():
    """Build container with boto3 mocked at the adapter level."""
    with (
        patch("deskai.adapters.auth.cognito_provider.boto3") as mock_cognito_boto,
        patch(
            "deskai.adapters.persistence.base_repository.boto3"
        ) as mock_dynamo,
        patch(
            "deskai.adapters.transcription.elevenlabs_config.boto3"
        ) as mock_secrets_boto,
        patch("deskai.adapters.storage.s3_client.boto3") as mock_s3_boto,
    ):
        mock_cognito_boto.client.return_value = MagicMock()
        mock_dynamo.resource.return_value.Table.return_value = MagicMock()
        mock_secrets_boto.client.return_value.get_secret_value.return_value = {
            "SecretString": _SECRET_VALUE
        }
        mock_s3_boto.client.return_value = MagicMock()
        return build_container()


class ContainerTranscriptionTest(unittest.TestCase):
    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_finalize_transcript(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(
            container.finalize_transcript, FinalizeTranscriptUseCase
        )

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_transcription_provider(self) -> None:
        from deskai.ports.transcription_provider import TranscriptionProvider

        container = _build_with_mocked_boto()
        self.assertIsInstance(
            container.transcription_provider, TranscriptionProvider
        )

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_transcript_repo(self) -> None:
        from deskai.ports.transcript_repository import TranscriptRepository

        container = _build_with_mocked_boto()
        self.assertIsInstance(
            container.transcript_repo, TranscriptRepository
        )

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_pause_session(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(container.pause_session, PauseSessionUseCase)

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_resume_session(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(container.resume_session, ResumeSessionUseCase)

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_issue_transcription_token(self) -> None:
        container = _build_with_mocked_boto()
        self.assertIsInstance(
            container.issue_transcription_token,
            IssueTranscriptionTokenUseCase,
        )

    @patch.dict(os.environ, _REQUIRED_ENV, clear=False)
    def test_container_has_transcript_segment_repo(self) -> None:
        from deskai.ports.transcript_segment_repository import (
            TranscriptSegmentRepository,
        )

        container = _build_with_mocked_boto()
        self.assertIsInstance(
            container.transcript_segment_repo, TranscriptSegmentRepository
        )


if __name__ == "__main__":
    unittest.main()
