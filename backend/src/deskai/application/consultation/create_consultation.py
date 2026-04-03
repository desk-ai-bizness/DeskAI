"""Create a new consultation for a patient."""

from dataclasses import dataclass

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.auth.exceptions import PlanLimitExceededError, TrialExpiredError
from deskai.domain.auth.services import compute_entitlements
from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.consultation.rules import validate_consultation_creation
from deskai.domain.patient.exceptions import PatientNotFoundError, PatientValidationError
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.doctor_repository import DoctorRepository
from deskai.ports.patient_repository import PatientRepository
from deskai.shared.identifiers import new_uuid
from deskai.shared.time import utc_now_iso


@dataclass(frozen=True)
class CreateConsultationUseCase:
    """Validate inputs, check plan entitlement, persist consultation, and emit audit event."""

    consultation_repo: ConsultationRepository
    patient_repo: PatientRepository
    audit_repo: AuditRepository
    doctor_repo: DoctorRepository

    def execute(
        self,
        auth_context: AuthContext,
        patient_id: str,
        specialty: str,
        scheduled_date: str,
        notes: str = "",
    ) -> Consultation:
        errors = validate_consultation_creation(
            patient_id, auth_context.doctor_id, auth_context.clinic_id, specialty
        )
        if errors:
            raise PatientValidationError(errors[0])

        used = self.doctor_repo.count_consultations_this_month(auth_context.doctor_id)
        created_at = self.doctor_repo.find_created_at(auth_context.doctor_id)
        entitlements = compute_entitlements(
            plan_type=auth_context.plan_type,
            created_at=created_at or "",
            consultations_used_this_month=used,
        )
        if entitlements.trial_expired:
            raise TrialExpiredError("Free trial period has expired")
        if not entitlements.can_create_consultation:
            raise PlanLimitExceededError(
                f"Monthly consultation limit reached ({used}/{used})"
            )

        patient = self.patient_repo.find_by_id(patient_id, auth_context.clinic_id)
        if not patient:
            raise PatientNotFoundError(f"Patient {patient_id} not found")

        now = utc_now_iso()
        consultation = Consultation(
            consultation_id=new_uuid(),
            clinic_id=auth_context.clinic_id,
            doctor_id=auth_context.doctor_id,
            patient_id=patient_id,
            specialty=specialty,
            status=ConsultationStatus.STARTED,
            scheduled_date=scheduled_date,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

        self.consultation_repo.save(consultation)

        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation.consultation_id,
                event_type=AuditAction.CONSULTATION_CREATED,
                actor_id=auth_context.doctor_id,
                timestamp=consultation.created_at,
                payload={"patient_id": patient_id, "specialty": specialty},
            )
        )

        return consultation
