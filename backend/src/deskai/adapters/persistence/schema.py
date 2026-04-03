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
