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
