"""Dependency wiring entrypoint for backend handlers."""

from dataclasses import dataclass

from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
from deskai.adapters.export.pdf_generator import PdfExportGenerator
from deskai.adapters.llm.lazy_provider import LazyLLMProvider
from deskai.adapters.persistence.dynamodb_audit_repository import (
    DynamoDBAuditRepository,
)
from deskai.adapters.persistence.dynamodb_connection_repository import (
    DynamoDBConnectionRepository,
)
from deskai.adapters.persistence.dynamodb_consultation_repository import (
    DynamoDBConsultationRepository,
)
from deskai.adapters.persistence.dynamodb_doctor_repository import (
    DynamoDBDoctorRepository,
)
from deskai.adapters.persistence.dynamodb_patient_repository import (
    DynamoDBPatientRepository,
)
from deskai.adapters.persistence.dynamodb_session_repository import (
    DynamoDBSessionRepository,
)
from deskai.application.ai_pipeline.run_pipeline import (
    RunPipelineUseCase,
)
from deskai.application.auth.authenticate import AuthenticateUseCase
from deskai.application.auth.check_entitlements import (
    CheckEntitlementsUseCase,
)
from deskai.application.auth.forgot_password import (
    ConfirmForgotPasswordUseCase,
    ForgotPasswordUseCase,
)
from deskai.application.auth.get_current_user import (
    GetCurrentUserUseCase,
)
from deskai.application.auth.sign_out import SignOutUseCase
from deskai.application.config.get_ui_config import (
    GetUiConfigUseCase,
)
from deskai.application.consultation.create_consultation import (
    CreateConsultationUseCase,
)
from deskai.application.consultation.get_consultation import (
    GetConsultationUseCase,
)
from deskai.application.consultation.list_consultations import (
    ListConsultationsUseCase,
)
from deskai.application.export.generate_export import (
    GenerateExportUseCase,
)
from deskai.application.patient.create_patient import (
    CreatePatientUseCase,
)
from deskai.application.patient.get_patient_detail import (
    GetPatientDetailUseCase,
)
from deskai.application.patient.list_patients import (
    ListPatientsUseCase,
)
from deskai.application.review.finalize_consultation import (
    FinalizeConsultationUseCase,
)
from deskai.application.review.open_review import (
    OpenReviewUseCase,
)
from deskai.application.review.update_review import (
    UpdateReviewUseCase,
)
from deskai.application.session.end_session import EndSessionUseCase
from deskai.application.session.pause_session import PauseSessionUseCase
from deskai.application.session.resume_session import ResumeSessionUseCase
from deskai.application.session.start_session import StartSessionUseCase
from deskai.application.transcription.finalize_transcript import (
    FinalizeTranscriptUseCase,
)
from deskai.application.transcription.issue_transcription_token import (
    IssueTranscriptionTokenUseCase,
)
from deskai.bff.ui_config.bff_assembler_adapter import (
    BffUiConfigAssembler,
)
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.auth_provider import AuthProvider
from deskai.ports.connection_repository import ConnectionRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.doctor_repository import DoctorRepository
from deskai.ports.event_publisher import EventPublisher
from deskai.ports.export_generator import ExportGenerator
from deskai.ports.llm_provider import LLMProvider
from deskai.ports.patient_repository import PatientRepository
from deskai.ports.session_repository import SessionRepository
from deskai.ports.storage_provider import StorageProvider
from deskai.ports.transcript_repository import TranscriptRepository
from deskai.ports.transcript_segment_repository import TranscriptSegmentRepository
from deskai.ports.transcription_provider import TranscriptionProvider
from deskai.ports.transcription_token_provider import TranscriptionTokenProvider
from deskai.ports.ui_config_assembler import UiConfigAssembler
from deskai.shared.config import Settings, load_settings
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


@dataclass(frozen=True)
class Container:
    """Resolved runtime dependencies for handler execution."""

    settings: Settings
    auth_provider: AuthProvider
    doctor_repo: DoctorRepository
    consultation_repo: ConsultationRepository
    patient_repo: PatientRepository
    session_repo: SessionRepository
    connection_repo: ConnectionRepository
    audit_repo: AuditRepository
    transcription_provider: TranscriptionProvider
    transcription_token_provider: TranscriptionTokenProvider
    transcript_repo: TranscriptRepository
    transcript_segment_repo: TranscriptSegmentRepository
    artifact_repo: ArtifactRepository
    event_publisher: EventPublisher
    export_generator: ExportGenerator
    storage_provider: StorageProvider
    llm_provider: LLMProvider
    ui_config_assembler: UiConfigAssembler
    authenticate: AuthenticateUseCase
    sign_out: SignOutUseCase
    forgot_password: ForgotPasswordUseCase
    confirm_forgot_password: ConfirmForgotPasswordUseCase
    get_current_user: GetCurrentUserUseCase
    check_entitlements: CheckEntitlementsUseCase
    create_consultation: CreateConsultationUseCase
    get_consultation: GetConsultationUseCase
    list_consultations: ListConsultationsUseCase
    create_patient: CreatePatientUseCase
    list_patients: ListPatientsUseCase
    get_patient_detail: GetPatientDetailUseCase
    start_session: StartSessionUseCase
    end_session: EndSessionUseCase
    pause_session: PauseSessionUseCase
    resume_session: ResumeSessionUseCase
    issue_transcription_token: IssueTranscriptionTokenUseCase
    finalize_transcript: FinalizeTranscriptUseCase
    run_pipeline: RunPipelineUseCase
    get_ui_config: GetUiConfigUseCase
    open_review: OpenReviewUseCase
    update_review: UpdateReviewUseCase
    finalize_consultation: FinalizeConsultationUseCase
    generate_export: GenerateExportUseCase


def build_container() -> Container:
    """Create the dependency container with all wiring."""
    import time

    from deskai.adapters.storage.s3_artifact_repository import (
        S3ArtifactRepository,
    )
    from deskai.adapters.storage.s3_client import S3Client
    from deskai.adapters.storage.s3_transcript_repository import (
        S3TranscriptRepository,
    )
    from deskai.adapters.transcription.lazy_provider import (
        LazyTranscriptionProvider,
    )

    start = time.monotonic()
    logger.info("container_build_started")

    settings = load_settings()

    if not settings.cognito_user_pool_id or not settings.cognito_client_id:
        logger.error("container_build_failed", extra=log_context(reason="missing_cognito_config"))
        raise RuntimeError(
            "DESKAI_COGNITO_USER_POOL_ID and DESKAI_COGNITO_CLIENT_ID "
            "environment variables are required."
        )

    doctor_repo = DynamoDBDoctorRepository(
        table_name=settings.dynamodb_table,
    )
    auth_provider = CognitoAuthProvider(
        user_pool_id=settings.cognito_user_pool_id,
        client_id=settings.cognito_client_id,
        doctor_repo=doctor_repo,
    )
    consultation_repo = DynamoDBConsultationRepository(
        table_name=settings.dynamodb_table,
    )
    patient_repo = DynamoDBPatientRepository(
        table_name=settings.dynamodb_table,
    )
    session_repo = DynamoDBSessionRepository(
        table_name=settings.dynamodb_table,
    )
    connection_repo = DynamoDBConnectionRepository(
        table_name=settings.dynamodb_table,
    )
    audit_repo = DynamoDBAuditRepository(
        table_name=settings.dynamodb_table,
    )

    s3_client = S3Client(bucket_name=settings.artifacts_bucket)

    def _build_transcription_provider():
        from deskai.adapters.transcription.elevenlabs_config import (
            load_elevenlabs_config,
        )
        from deskai.adapters.transcription.elevenlabs_provider import (
            ElevenLabsScribeProvider,
        )

        config = load_elevenlabs_config(settings.elevenlabs_secret_name)
        return ElevenLabsScribeProvider(config=config, s3_client=s3_client)

    transcription_provider = LazyTranscriptionProvider(_build_transcription_provider)
    transcript_repo = S3TranscriptRepository(s3_client=s3_client)
    artifact_repo = S3ArtifactRepository(s3_client=s3_client)

    from deskai.adapters.persistence.dynamodb_transcript_segment_repository import (
        DynamoDBTranscriptSegmentRepository,
    )
    from deskai.adapters.transcription.elevenlabs_token_provider import (
        ElevenLabsTokenProvider,
    )

    transcript_segment_repo = DynamoDBTranscriptSegmentRepository(
        table_name=settings.dynamodb_table,
    )

    from deskai.adapters.transcription.lazy_token_provider import (
        LazyTranscriptionTokenProvider,
    )

    def _build_token_provider():
        from deskai.adapters.transcription.elevenlabs_config import (
            load_elevenlabs_config,
        )

        config = load_elevenlabs_config(settings.elevenlabs_secret_name)
        return ElevenLabsTokenProvider(config=config)

    transcription_token_provider = LazyTranscriptionTokenProvider(_build_token_provider)

    from deskai.adapters.events.eventbridge_publisher import EventBridgePublisher
    from deskai.adapters.storage.s3_storage_provider import (
        S3StorageProvider,
    )

    event_publisher = EventBridgePublisher(event_bus_name=settings.event_bus_name)
    export_generator = PdfExportGenerator()
    storage_provider = S3StorageProvider(s3_client=s3_client)

    def _build_llm_provider():
        from deskai.adapters.secrets.secrets_manager import (
            SecretsManagerClient,
        )

        secrets = SecretsManagerClient()

        if settings.llm_provider == "gemini":
            from deskai.adapters.llm.gemini_provider import GeminiLLMProvider

            secret = secrets.get_secret(settings.gemini_secret_name)
            return GeminiLLMProvider(api_key=secret["api_key"])

        from deskai.adapters.llm.claude_provider import ClaudeLLMProvider

        secret = secrets.get_secret(settings.claude_secret_name)
        return ClaudeLLMProvider(api_key=secret["api_key"])

    llm_provider = LazyLLMProvider(_build_llm_provider)
    ui_config_assembler = BffUiConfigAssembler()

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        "container_build_completed",
        extra=log_context(duration_ms=duration_ms, table=settings.dynamodb_table),
    )

    return Container(
        settings=settings,
        auth_provider=auth_provider,
        doctor_repo=doctor_repo,
        consultation_repo=consultation_repo,
        patient_repo=patient_repo,
        session_repo=session_repo,
        connection_repo=connection_repo,
        audit_repo=audit_repo,
        transcription_provider=transcription_provider,
        transcription_token_provider=transcription_token_provider,
        transcript_repo=transcript_repo,
        transcript_segment_repo=transcript_segment_repo,
        artifact_repo=artifact_repo,
        event_publisher=event_publisher,
        export_generator=export_generator,
        storage_provider=storage_provider,
        llm_provider=llm_provider,
        ui_config_assembler=ui_config_assembler,
        authenticate=AuthenticateUseCase(
            auth_provider=auth_provider,
        ),
        sign_out=SignOutUseCase(
            auth_provider=auth_provider,
        ),
        forgot_password=ForgotPasswordUseCase(
            auth_provider=auth_provider,
        ),
        confirm_forgot_password=ConfirmForgotPasswordUseCase(
            auth_provider=auth_provider,
        ),
        get_current_user=GetCurrentUserUseCase(
            doctor_repo=doctor_repo,
        ),
        check_entitlements=CheckEntitlementsUseCase(
            doctor_repo=doctor_repo,
        ),
        create_consultation=CreateConsultationUseCase(
            consultation_repo=consultation_repo,
            patient_repo=patient_repo,
            audit_repo=audit_repo,
            doctor_repo=doctor_repo,
        ),
        get_consultation=GetConsultationUseCase(
            consultation_repo=consultation_repo,
        ),
        list_consultations=ListConsultationsUseCase(
            consultation_repo=consultation_repo,
        ),
        create_patient=CreatePatientUseCase(
            patient_repo=patient_repo,
        ),
        list_patients=ListPatientsUseCase(
            patient_repo=patient_repo,
        ),
        get_patient_detail=GetPatientDetailUseCase(
            patient_repo=patient_repo,
            consultation_repo=consultation_repo,
            artifact_repo=artifact_repo,
        ),
        start_session=StartSessionUseCase(
            consultation_repo=consultation_repo,
            session_repo=session_repo,
            audit_repo=audit_repo,
        ),
        end_session=EndSessionUseCase(
            consultation_repo=consultation_repo,
            session_repo=session_repo,
            audit_repo=audit_repo,
            event_publisher=event_publisher,
        ),
        pause_session=PauseSessionUseCase(
            session_repo=session_repo,
            audit_repo=audit_repo,
        ),
        resume_session=ResumeSessionUseCase(
            session_repo=session_repo,
            audit_repo=audit_repo,
        ),
        issue_transcription_token=IssueTranscriptionTokenUseCase(
            consultation_repo=consultation_repo,
            transcription_token_provider=transcription_token_provider,
            audit_repo=audit_repo,
        ),
        finalize_transcript=FinalizeTranscriptUseCase(
            transcription_provider=transcription_provider,
            transcript_repo=transcript_repo,
            consultation_repo=consultation_repo,
            audit_repo=audit_repo,
        ),
        run_pipeline=RunPipelineUseCase(
            llm_provider=llm_provider,
            artifact_repo=artifact_repo,
            consultation_repo=consultation_repo,
            transcript_repo=transcript_repo,
            patient_repo=patient_repo,
            audit_repo=audit_repo,
        ),
        get_ui_config=GetUiConfigUseCase(
            ui_config_assembler=ui_config_assembler,
        ),
        open_review=OpenReviewUseCase(
            consultation_repo=consultation_repo,
            artifact_repo=artifact_repo,
            audit_repo=audit_repo,
            transcript_segment_repo=transcript_segment_repo,
        ),
        update_review=UpdateReviewUseCase(
            consultation_repo=consultation_repo,
            artifact_repo=artifact_repo,
            audit_repo=audit_repo,
        ),
        finalize_consultation=FinalizeConsultationUseCase(
            consultation_repo=consultation_repo,
            artifact_repo=artifact_repo,
            audit_repo=audit_repo,
        ),
        generate_export=GenerateExportUseCase(
            consultation_repo=consultation_repo,
            artifact_repo=artifact_repo,
            export_generator=export_generator,
            storage_provider=storage_provider,
            audit_repo=audit_repo,
        ),
    )
