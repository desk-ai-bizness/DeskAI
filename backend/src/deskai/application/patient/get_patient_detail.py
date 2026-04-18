"""Get patient detail with current-doctor-only consultation history."""

from dataclasses import dataclass
from typing import Any

from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.entities import Consultation, ConsultationStatus
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.patient.entities import Patient
from deskai.domain.patient.exceptions import PatientNotFoundError
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.patient_repository import PatientRepository
from deskai.shared.logging import get_logger, log_context

logger = get_logger()


@dataclass(frozen=True)
class PatientHistoryItem:
    """Safe patient-history item for BFF rendering."""

    consultation: Consultation
    preview: dict[str, str] | None = None


@dataclass(frozen=True)
class PatientDetailResult:
    """Patient detail plus authorized current-doctor consultation history."""

    patient: Patient
    history: list[PatientHistoryItem]


@dataclass(frozen=True)
class GetPatientDetailUseCase:
    """Load one clinic patient and only the requesting doctor's consultations."""

    patient_repo: PatientRepository
    consultation_repo: ConsultationRepository
    artifact_repo: ArtifactRepository

    def execute(self, auth_context: AuthContext, patient_id: str) -> PatientDetailResult:
        patient = self.patient_repo.find_by_id(patient_id, auth_context.clinic_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found")

        consultations = self.consultation_repo.find_by_patient_for_doctor(
            clinic_id=auth_context.clinic_id,
            patient_id=patient_id,
            doctor_id=auth_context.doctor_id,
        )
        history = [
            PatientHistoryItem(
                consultation=consultation,
                preview=self._build_preview(auth_context.clinic_id, consultation),
            )
            for consultation in consultations
        ]

        logger.debug(
            "patient_detail_loaded",
            extra=log_context(
                patient_id=patient_id,
                clinic_id=auth_context.clinic_id,
                doctor_id=auth_context.doctor_id,
                history_count=len(history),
            ),
        )
        return PatientDetailResult(patient=patient, history=history)

    def _build_preview(
        self, clinic_id: str, consultation: Consultation
    ) -> dict[str, str] | None:
        if consultation.status != ConsultationStatus.FINALIZED:
            return None

        final_record = self.artifact_repo.get_artifact(
            clinic_id, consultation.consultation_id, ArtifactType.FINAL_VERSION
        )
        summary = self._extract_summary(final_record)
        if not summary:
            return None
        return {"summary": summary}

    @staticmethod
    def _extract_summary(final_record: dict[str, Any] | None) -> str | None:
        if not final_record:
            return None
        summary = final_record.get("summary")
        if isinstance(summary, str):
            return summary
        if not isinstance(summary, dict):
            return None
        content = summary.get("content") or summary.get("resumo") or summary.get("texto")
        if isinstance(content, str):
            return content
        return None
