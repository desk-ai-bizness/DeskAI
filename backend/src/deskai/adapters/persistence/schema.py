"""Canonical DynamoDB field names for the doctor profile record.

This module is the **single source of truth** for the attribute names stored
in the ``DOCTOR#<id> / PROFILE`` item.  It must be used by:

* the repository adapter (reads)
* the seed / migration scripts (writes)
* the test fixtures (mocked DynamoDB items)

Keeping field names in one place prevents schema drift between layers.
"""


class DoctorProfileFields:
    """DynamoDB attribute names for a doctor profile item."""

    PK = "PK"
    SK = "SK"
    DOCTOR_ID = "doctor_id"
    EMAIL = "email"
    FULL_NAME = "full_name"
    CLINIC_ID = "clinic_id"
    CLINIC_NAME = "clinic_name"
    PLAN_TYPE = "plan_type"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    COGNITO_SUB = "cognito_sub"
    SPECIALTY = "specialty"

    # Legacy alias written by older code paths.
    LEGACY_NAME = "name"

    @classmethod
    def build_item(
        cls,
        *,
        identity_provider_id: str,
        doctor_id: str,
        email: str,
        full_name: str,
        clinic_id: str,
        clinic_name: str,
        plan_type: str,
        created_at: str,
        updated_at: str | None = None,
        specialty: str = "general_practice",
    ) -> dict[str, str]:
        """Build a canonical DynamoDB item dict for a doctor profile."""
        item = {
            cls.PK: f"DOCTOR#{identity_provider_id}",
            cls.SK: "PROFILE",
            cls.DOCTOR_ID: doctor_id,
            cls.EMAIL: email,
            cls.FULL_NAME: full_name,
            cls.LEGACY_NAME: full_name,
            cls.CLINIC_ID: clinic_id,
            cls.CLINIC_NAME: clinic_name,
            cls.PLAN_TYPE: plan_type,
            cls.CREATED_AT: created_at,
            cls.UPDATED_AT: updated_at or created_at,
            cls.COGNITO_SUB: identity_provider_id,
            cls.SPECIALTY: specialty,
        }
        return item


class ConsultationFields:
    """DynamoDB attribute names for a consultation item."""

    PK = "PK"
    SK = "SK"
    GSI1PK = "GSI1PK"
    GSI1SK = "GSI1SK"
    CONSULTATION_ID = "consultation_id"
    CLINIC_ID = "clinic_id"
    DOCTOR_ID = "doctor_id"
    PATIENT_ID = "patient_id"
    SPECIALTY = "specialty"
    STATUS = "status"
    SCHEDULED_DATE = "scheduled_date"
    NOTES = "notes"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    SESSION_STARTED_AT = "session_started_at"
    SESSION_ENDED_AT = "session_ended_at"
    PROCESSING_STARTED_AT = "processing_started_at"
    PROCESSING_COMPLETED_AT = "processing_completed_at"
    REVIEW_OPENED_AT = "review_opened_at"
    FINALIZED_AT = "finalized_at"
    FINALIZED_BY = "finalized_by"
    ERROR_DETAILS = "error_details"

    @classmethod
    def build_item(
        cls,
        *,
        consultation_id: str,
        clinic_id: str,
        doctor_id: str,
        patient_id: str,
        specialty: str,
        status: str,
        scheduled_date: str,
        notes: str,
        created_at: str,
        updated_at: str,
        session_started_at: str | None = None,
        session_ended_at: str | None = None,
        processing_started_at: str | None = None,
        processing_completed_at: str | None = None,
        review_opened_at: str | None = None,
        finalized_at: str | None = None,
        finalized_by: str | None = None,
        error_details: str | None = None,
    ) -> dict[str, object]:
        """Build a canonical DynamoDB item dict for a consultation."""
        item: dict[str, object] = {
            cls.PK: f"CLINIC#{clinic_id}",
            cls.SK: f"CONSULTATION#{consultation_id}",
            cls.GSI1PK: f"DOCTOR#{doctor_id}",
            cls.GSI1SK: f"CONSULTATION#{scheduled_date}#{consultation_id}",
            cls.CONSULTATION_ID: consultation_id,
            cls.CLINIC_ID: clinic_id,
            cls.DOCTOR_ID: doctor_id,
            cls.PATIENT_ID: patient_id,
            cls.SPECIALTY: specialty,
            cls.STATUS: status,
            cls.SCHEDULED_DATE: scheduled_date,
            cls.NOTES: notes,
            cls.CREATED_AT: created_at,
            cls.UPDATED_AT: updated_at,
        }
        optional = {
            cls.SESSION_STARTED_AT: session_started_at,
            cls.SESSION_ENDED_AT: session_ended_at,
            cls.PROCESSING_STARTED_AT: processing_started_at,
            cls.PROCESSING_COMPLETED_AT: processing_completed_at,
            cls.REVIEW_OPENED_AT: review_opened_at,
            cls.FINALIZED_AT: finalized_at,
            cls.FINALIZED_BY: finalized_by,
            cls.ERROR_DETAILS: error_details,
        }
        for key, value in optional.items():
            if value is not None:
                item[key] = value
        return item


class SessionFields:
    """DynamoDB attribute names for a session item."""

    PK = "PK"
    SK = "SK"
    GSI1PK = "GSI1PK"
    GSI1SK = "GSI1SK"
    SESSION_ID = "session_id"
    CONSULTATION_ID = "consultation_id"
    DOCTOR_ID = "doctor_id"
    CLINIC_ID = "clinic_id"
    STATE = "state"
    STARTED_AT = "started_at"
    ENDED_AT = "ended_at"
    DURATION_SECONDS = "duration_seconds"
    AUDIO_CHUNKS_RECEIVED = "audio_chunks_received"
    CONNECTION_ID = "connection_id"
    GRACE_PERIOD_EXPIRES_AT = "grace_period_expires_at"
    LAST_ACTIVITY_AT = "last_activity_at"

    @classmethod
    def build_item(
        cls,
        *,
        session_id: str,
        consultation_id: str,
        doctor_id: str,
        clinic_id: str,
        state: str,
        started_at: str,
        duration_seconds: int = 0,
        audio_chunks_received: int = 0,
        ended_at: str | None = None,
        connection_id: str | None = None,
        grace_period_expires_at: str | None = None,
        last_activity_at: str | None = None,
    ) -> dict[str, object]:
        """Build a canonical DynamoDB item dict for a session."""
        item: dict[str, object] = {
            cls.PK: f"SESSION#{session_id}",
            cls.SK: "METADATA",
            cls.GSI1PK: f"CONSULTATION#{consultation_id}",
            cls.GSI1SK: f"SESSION#{session_id}",
            cls.SESSION_ID: session_id,
            cls.CONSULTATION_ID: consultation_id,
            cls.DOCTOR_ID: doctor_id,
            cls.CLINIC_ID: clinic_id,
            cls.STATE: state,
            cls.STARTED_AT: started_at,
            cls.DURATION_SECONDS: duration_seconds,
            cls.AUDIO_CHUNKS_RECEIVED: audio_chunks_received,
        }
        optional = {
            cls.ENDED_AT: ended_at,
            cls.CONNECTION_ID: connection_id,
            cls.GRACE_PERIOD_EXPIRES_AT: grace_period_expires_at,
            cls.LAST_ACTIVITY_AT: last_activity_at,
        }
        for key, value in optional.items():
            if value is not None:
                item[key] = value
        return item


class PatientFields:
    """DynamoDB attribute names for a patient item."""

    PK = "PK"
    SK = "SK"
    PATIENT_ID = "patient_id"
    NAME = "name"
    DATE_OF_BIRTH = "date_of_birth"
    CLINIC_ID = "clinic_id"
    CREATED_AT = "created_at"

    @classmethod
    def build_item(
        cls,
        *,
        patient_id: str,
        name: str,
        date_of_birth: str,
        clinic_id: str,
        created_at: str,
    ) -> dict[str, str]:
        """Build a canonical DynamoDB item dict for a patient."""
        return {
            cls.PK: f"CLINIC#{clinic_id}",
            cls.SK: f"PATIENT#{patient_id}",
            cls.PATIENT_ID: patient_id,
            cls.NAME: name,
            cls.DATE_OF_BIRTH: date_of_birth,
            cls.CLINIC_ID: clinic_id,
            cls.CREATED_AT: created_at,
        }


class AuditFields:
    """DynamoDB attribute names for an audit event item."""

    PK = "PK"
    SK = "SK"
    EVENT_ID = "event_id"
    CONSULTATION_ID = "consultation_id"
    EVENT_TYPE = "event_type"
    ACTOR_ID = "actor_id"
    TIMESTAMP = "timestamp"
    PAYLOAD = "payload"

    @classmethod
    def build_item(
        cls,
        *,
        event_id: str,
        consultation_id: str,
        event_type: str,
        actor_id: str,
        timestamp: str,
        payload: str | None = None,
    ) -> dict[str, object]:
        """Build a canonical DynamoDB item dict for an audit event."""
        item: dict[str, object] = {
            cls.PK: f"CONSULTATION#{consultation_id}",
            cls.SK: f"AUDIT#{timestamp}#{event_id}",
            cls.EVENT_ID: event_id,
            cls.CONSULTATION_ID: consultation_id,
            cls.EVENT_TYPE: event_type,
            cls.ACTOR_ID: actor_id,
            cls.TIMESTAMP: timestamp,
        }
        if payload is not None:
            item[cls.PAYLOAD] = payload
        return item


class ConnectionFields:
    """DynamoDB attribute names for a WebSocket connection item."""

    PK = "PK"
    SK = "SK"
    CONNECTION_ID = "connection_id"
    SESSION_ID = "session_id"
    DOCTOR_ID = "doctor_id"
    CLINIC_ID = "clinic_id"
    CONNECTED_AT = "connected_at"

    @classmethod
    def build_item(
        cls,
        *,
        connection_id: str,
        session_id: str,
        doctor_id: str,
        clinic_id: str,
        connected_at: str,
    ) -> dict[str, str]:
        """Build a canonical DynamoDB item dict for a connection."""
        return {
            cls.PK: f"CONNECTION#{connection_id}",
            cls.SK: "METADATA",
            cls.CONNECTION_ID: connection_id,
            cls.SESSION_ID: session_id,
            cls.DOCTOR_ID: doctor_id,
            cls.CLINIC_ID: clinic_id,
            cls.CONNECTED_AT: connected_at,
        }
