"""Dependency wiring entrypoint for backend handlers."""

from dataclasses import dataclass

from deskai.adapters.auth.cognito_provider import CognitoAuthProvider
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
from deskai.application.patient.create_patient import (
    CreatePatientUseCase,
)
from deskai.application.patient.list_patients import (
    ListPatientsUseCase,
)
from deskai.application.session.end_session import EndSessionUseCase
from deskai.application.session.start_session import StartSessionUseCase
from deskai.application.transcription.finalize_transcript import (
    FinalizeTranscriptUseCase,
)
from deskai.application.transcription.process_audio_chunk import (
    ProcessAudioChunkUseCase,
)
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.auth_provider import AuthProvider
from deskai.ports.connection_repository import ConnectionRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.doctor_repository import DoctorRepository
from deskai.ports.patient_repository import PatientRepository
from deskai.ports.session_repository import SessionRepository
from deskai.ports.transcript_repository import TranscriptRepository
from deskai.ports.transcription_provider import TranscriptionProvider
from deskai.shared.config import Settings, load_settings


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
    transcript_repo: TranscriptRepository
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
    start_session: StartSessionUseCase
    end_session: EndSessionUseCase
    process_audio_chunk: ProcessAudioChunkUseCase
    finalize_transcript: FinalizeTranscriptUseCase
    get_ui_config: GetUiConfigUseCase


def build_container() -> Container:
    """Create the dependency container with all wiring."""
    from deskai.adapters.storage.s3_client import S3Client
    from deskai.adapters.storage.s3_transcript_repository import (
        S3TranscriptRepository,
    )
    from deskai.adapters.transcription.elevenlabs_config import (
        load_elevenlabs_config,
    )
    from deskai.adapters.transcription.elevenlabs_provider import (
        ElevenLabsScribeProvider,
    )

    settings = load_settings()

    if not settings.cognito_user_pool_id or not settings.cognito_client_id:
        raise RuntimeError(
            "DESKAI_COGNITO_USER_POOL_ID and DESKAI_COGNITO_CLIENT_ID "
            "environment variables are required."
        )

    auth_provider = CognitoAuthProvider(
        user_pool_id=settings.cognito_user_pool_id,
        client_id=settings.cognito_client_id,
    )
    doctor_repo = DynamoDBDoctorRepository(
        table_name=settings.dynamodb_table,
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

    elevenlabs_config = load_elevenlabs_config(settings.elevenlabs_secret_name)
    transcription_provider = ElevenLabsScribeProvider(config=elevenlabs_config)

    s3_client = S3Client(bucket_name=settings.artifacts_bucket)
    transcript_repo = S3TranscriptRepository(s3_client=s3_client)

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
        transcript_repo=transcript_repo,
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
        start_session=StartSessionUseCase(
            consultation_repo=consultation_repo,
            session_repo=session_repo,
            audit_repo=audit_repo,
        ),
        end_session=EndSessionUseCase(
            consultation_repo=consultation_repo,
            session_repo=session_repo,
            audit_repo=audit_repo,
        ),
        process_audio_chunk=ProcessAudioChunkUseCase(
            session_repo=session_repo,
            transcription_provider=transcription_provider,
        ),
        finalize_transcript=FinalizeTranscriptUseCase(
            transcription_provider=transcription_provider,
            transcript_repo=transcript_repo,
            consultation_repo=consultation_repo,
            audit_repo=audit_repo,
        ),
        get_ui_config=GetUiConfigUseCase(),
    )
