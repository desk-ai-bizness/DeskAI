"""Shared testing fixtures and helpers for backend tests."""

import json
from typing import Any
from unittest.mock import MagicMock

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.value_objects import (
    AuthContext,
    PlanType,
    Tokens,
)
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.patient.entities import Patient
from deskai.domain.transcription.entities import NormalizedTranscript
from deskai.domain.transcription.value_objects import CompletenessStatus, SpeakerSegment

# ---------------------------------------------------------------------------
# AWS client mocks
# ---------------------------------------------------------------------------


def make_mock_cognito_client() -> MagicMock:
    """Return a MagicMock pre-configured as a boto3 cognito-idp client."""
    client = MagicMock(name="cognito-idp-client")
    client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "test-access-token",
            "RefreshToken": "test-refresh-token",
            "ExpiresIn": 3600,
        }
    }
    return client


def make_mock_dynamodb_table() -> MagicMock:
    """Return a MagicMock pre-configured as a DynamoDB Table resource."""
    table = MagicMock(name="dynamodb-table")
    table.get_item.return_value = {}
    table.put_item.return_value = {}
    table.query.return_value = {"Items": []}
    return table


def make_mock_dynamodb_resource() -> MagicMock:
    """Return a MagicMock pre-configured as a boto3 DynamoDB resource."""
    resource = MagicMock(name="dynamodb-resource")
    resource.Table.return_value = make_mock_dynamodb_table()
    return resource


# ---------------------------------------------------------------------------
# Domain fixtures
# ---------------------------------------------------------------------------

SAMPLE_CREATED_AT = "2026-01-15T10:00:00+00:00"


def make_sample_doctor_profile(
    *,
    doctor_id: str = "doc-001",
    identity_provider_id: str = "cognito-sub-001",
    email: str = "dr.test@clinic.com",
    name: str = "Dr. Test",
    clinic_id: str = "clinic-001",
    clinic_name: str = "Test Clinic",
    plan_type: PlanType = PlanType.PLUS,
    created_at: str = SAMPLE_CREATED_AT,
) -> DoctorProfile:
    """Build a DoctorProfile with sensible defaults."""
    return DoctorProfile(
        doctor_id=doctor_id,
        identity_provider_id=identity_provider_id,
        email=email,
        name=name,
        clinic_id=clinic_id,
        clinic_name=clinic_name,
        plan_type=plan_type,
        created_at=created_at,
    )


def make_sample_tokens(
    *,
    access_token: str = "test-access-token",
    refresh_token: str = "test-refresh-token",
    expires_in: int = 3600,
) -> Tokens:
    """Build a Tokens value object with sensible defaults."""
    return Tokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


def make_sample_auth_context(
    *,
    doctor_id: str = "doc-001",
    email: str = "dr.test@clinic.com",
    clinic_id: str = "clinic-001",
    plan_type: PlanType = PlanType.PLUS,
) -> AuthContext:
    """Build an AuthContext value object with sensible defaults."""
    return AuthContext(
        doctor_id=doctor_id,
        email=email,
        clinic_id=clinic_id,
        plan_type=plan_type,
    )


# ---------------------------------------------------------------------------
# API Gateway v2 event builder
# ---------------------------------------------------------------------------


def make_apigw_event(
    *,
    path: str = "/v1/me",
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    cognito_sub: str = "cognito-sub-001",
    email: str = "dr.test@clinic.com",
    path_parameters: dict[str, str] | None = None,
    query_string_parameters: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build an HTTP API Gateway v2 event with customizable fields.

    The event includes a JWT authorizer section populated from
    *cognito_sub* and *email* so that ``extract_auth_context`` can
    resolve the caller identity.
    """
    event: dict[str, Any] = {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {
            "content-type": "application/json",
            **(headers or {}),
        },
        "requestContext": {
            "http": {
                "method": method,
                "path": path,
            },
            "authorizer": {
                "jwt": {
                    "claims": {
                        "sub": cognito_sub,
                        "email": email,
                    },
                },
            },
        },
    }

    if body is not None:
        event["body"] = json.dumps(body)

    if path_parameters is not None:
        event["pathParameters"] = path_parameters

    if query_string_parameters is not None:
        event["queryStringParameters"] = query_string_parameters

    return event


# ---------------------------------------------------------------------------
# Consultation / Patient / Audit fixtures
# ---------------------------------------------------------------------------


def make_sample_consultation(**overrides: Any) -> Consultation:
    """Build a Consultation entity with sensible defaults."""
    defaults: dict[str, Any] = dict(
        consultation_id="cons-001",
        clinic_id="clinic-001",
        doctor_id="doc-001",
        patient_id="pat-001",
        specialty="general_practice",
        status=ConsultationStatus.STARTED,
        scheduled_date="2026-04-01",
        notes="",
        created_at="2026-04-01T10:00:00+00:00",
        updated_at="2026-04-01T10:00:00+00:00",
    )
    defaults.update(overrides)
    return Consultation(**defaults)


def make_sample_patient(**overrides: Any) -> Patient:
    """Build a Patient entity with sensible defaults."""
    defaults: dict[str, Any] = dict(
        patient_id="pat-001",
        name="Joao Silva",
        date_of_birth="1990-05-15",
        clinic_id="clinic-001",
        created_at="2026-04-01T10:00:00+00:00",
    )
    defaults.update(overrides)
    return Patient(**defaults)


def make_sample_audit_event(**overrides: Any) -> AuditEvent:
    """Build an AuditEvent with sensible defaults."""
    defaults: dict[str, Any] = dict(
        event_id="evt-001",
        consultation_id="cons-001",
        event_type=AuditAction.CONSULTATION_CREATED,
        actor_id="doc-001",
        timestamp="2026-04-01T10:00:00+00:00",
        payload=None,
    )
    defaults.update(overrides)
    return AuditEvent(**defaults)


# ---------------------------------------------------------------------------
# AI Pipeline fixtures
# ---------------------------------------------------------------------------


def make_sample_normalized_transcript(**overrides: Any) -> NormalizedTranscript:
    """Build a NormalizedTranscript with sensible defaults."""
    defaults: dict[str, Any] = dict(
        consultation_id="cons-001",
        provider_name="elevenlabs",
        provider_session_id="sess-001",
        language="pt-BR",
        transcript_text=("Doutor: Como voce esta? Paciente: Estou com dor de cabeca ha dois dias."),
        speaker_segments=[
            SpeakerSegment(
                speaker="doctor",
                text="Como voce esta?",
                start_time=0.0,
                end_time=1.5,
                confidence=0.95,
            ),
            SpeakerSegment(
                speaker="patient",
                text="Estou com dor de cabeca ha dois dias.",
                start_time=2.0,
                end_time=4.0,
                confidence=0.90,
            ),
        ],
        completeness_status=CompletenessStatus.COMPLETE,
    )
    defaults.update(overrides)
    return NormalizedTranscript(**defaults)


def make_sample_anamnesis_output() -> dict[str, Any]:
    """Valid anamnesis JSON matching prompt schema."""
    return {
        "queixa_principal": {
            "descricao": "Dor de cabeca",
            "duracao": "2 dias",
        },
        "historia_doenca_atual": {
            "narrativa": "Paciente relata dor de cabeca...",
            "sintomas": [
                {
                    "nome": "cefaleia",
                    "inicio": "2 dias",
                    "intensidade": "moderada",
                    "fatores_agravantes": "nao_informado",
                    "fatores_atenuantes": "nao_informado",
                    "localizacao": "frontal",
                }
            ],
        },
        "historico_medico_pregresso": {
            "doencas_previas": [],
            "cirurgias_previas": [],
            "internacoes_previas": [],
        },
        "medicamentos_em_uso": [],
        "alergias": {"relatadas": [], "nega_alergias": False},
        "revisao_de_sistemas": {
            "sistemas_mencionados": [],
            "sistemas_nao_avaliados": ["cardiovascular", "respiratorio"],
        },
        "achados_exame_fisico": [],
        "observacoes_adicionais": "nao_informado",
        "campos_incompletos": ["achados_exame_fisico"],
    }


def make_sample_summary_output() -> dict[str, Any]:
    """Valid SOAP summary JSON matching prompt schema."""
    return {
        "subjetivo": {
            "queixa_principal": "Dor de cabeca",
            "historia": "Paciente relata cefaleia frontal ha 2 dias.",
            "informacoes_adicionais": "nao_informado",
        },
        "objetivo": {
            "exame_fisico": "nao_informado",
            "sinais_vitais": {
                "pressao_arterial": "nao_informado",
                "frequencia_cardiaca": "nao_informado",
                "temperatura": "nao_informado",
                "saturacao_o2": "nao_informado",
                "outros": "nao_informado",
            },
            "exames_complementares": "nao_informado",
        },
        "avaliacao": {
            "hipoteses_diagnosticas": [
                {
                    "descricao": "Cefaleia tensional",
                    "cid10_sugerido": "G44.2",
                    "confianca": "media",
                }
            ],
            "observacoes": "",
        },
        "plano": {
            "condutas": ["Orientacao sobre higiene do sono"],
            "exames_solicitados": [],
            "encaminhamentos": [],
            "prescricoes_mencionadas": [],
            "orientacoes_ao_paciente": ["Retornar se piora"],
            "retorno": "Se necessario",
        },
        "codigos_cid10_sugeridos": [
            {
                "codigo": "G44.2",
                "descricao": "Cefaleia tensional",
                "justificativa": "Relato de dor de cabeca frontal",
            }
        ],
        "aviso_revisao": (
            "Este resumo requer revisao e aprovacao do medico antes de ser finalizado."
        ),
    }


def make_sample_insights_output() -> dict[str, Any]:
    """Valid insights JSON matching prompt schema."""
    return {
        "observacoes": [
            {
                "categoria": "lacuna_de_documentacao",
                "descricao": "Exame fisico nao registrado",
                "severidade": "moderado",
                "evidencia": {
                    "trecho": "Estou com dor de cabeca ha dois dias",
                    "contexto": ("Paciente relata sintoma sem exame fisico documentado"),
                },
                "sugestao_revisao": "Registrar achados do exame fisico",
            }
        ],
        "resumo_observacoes": {
            "total": 1,
            "por_categoria": {
                "lacuna_de_documentacao": 1,
                "inconsistencia": 0,
                "atencao_clinica": 0,
            },
            "por_severidade": {
                "informativo": 0,
                "moderado": 1,
                "importante": 0,
            },
        },
        "aviso_revisao": (
            "Estas observacoes sao sinalizacoes para revisao. "
            "O medico e o responsavel pela avaliacao final."
        ),
    }
