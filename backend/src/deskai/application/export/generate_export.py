"""Generate a PDF export for a finalized consultation."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from deskai.domain.audit.entities import AuditAction, AuditEvent
from deskai.domain.auth.value_objects import AuthContext
from deskai.domain.consultation.exceptions import (
    ConsultationNotFoundError,
    ConsultationOwnershipError,
)
from deskai.domain.consultation.value_objects import ArtifactType
from deskai.domain.export.entities import ExportArtifact
from deskai.domain.export.exceptions import ExportGenerationError
from deskai.domain.export.services import build_export_s3_key
from deskai.domain.export.value_objects import ExportFormat
from deskai.domain.review.services import validate_export
from deskai.ports.artifact_repository import ArtifactRepository
from deskai.ports.audit_repository import AuditRepository
from deskai.ports.consultation_repository import ConsultationRepository
from deskai.ports.export_generator import ExportGenerator
from deskai.ports.storage_provider import StorageProvider
from deskai.shared.identifiers import new_uuid
from deskai.shared.logging import get_logger, log_context
from deskai.shared.time import utc_now_iso

logger = get_logger()

EXPORT_URL_EXPIRY_SECONDS = 3600  # 1 hour


@dataclass(frozen=True)
class GenerateExportUseCase:
    """Generate PDF export from finalized content, store in S3, return presigned URL."""

    consultation_repo: ConsultationRepository
    artifact_repo: ArtifactRepository
    export_generator: ExportGenerator
    storage_provider: StorageProvider
    audit_repo: AuditRepository

    def execute(
        self,
        auth_context: AuthContext,
        consultation_id: str,
        clinic_id: str,
    ) -> ExportArtifact:
        consultation = self.consultation_repo.find_by_id(consultation_id, clinic_id)
        if consultation is None:
            raise ConsultationNotFoundError(f"Consultation {consultation_id} not found")
        if consultation.doctor_id != auth_context.doctor_id:
            raise ConsultationOwnershipError("Requesting doctor does not own this consultation")

        validate_export(consultation_id, consultation.status)

        # Load finalized artifacts
        final_version = self.artifact_repo.get_artifact(
            clinic_id, consultation_id, ArtifactType.FINAL_VERSION
        )
        if final_version is None:
            raise ExportGenerationError(consultation_id, "Finalized record not found in storage")

        metadata = {
            "scheduled_date": consultation.scheduled_date,
            "specialty": consultation.specialty,
            "finalized_at": consultation.finalized_at,
        }

        # Generate PDF
        try:
            result = self.export_generator.generate(
                consultation_id=consultation_id,
                fmt=ExportFormat.PDF,
                metadata=metadata,
                medical_history=final_version.get("medical_history", {}),
                summary=final_version.get("summary", {}),
                accepted_insights=final_version.get("accepted_insights", []),
            )
        except Exception as exc:
            logger.error(
                "export_generation_failed",
                extra=log_context(
                    consultation_id=consultation_id,
                    error=str(exc),
                ),
            )
            raise ExportGenerationError(consultation_id, str(exc)) from exc

        # Store PDF in S3
        s3_key = build_export_s3_key(clinic_id, consultation_id)
        self.storage_provider.put(s3_key, result.data, "application/pdf")

        # Generate presigned URL
        presigned_url = self.storage_provider.generate_presigned_url(
            s3_key, EXPORT_URL_EXPIRY_SECONDS
        )

        expires_at = (
            datetime.now(tz=UTC) + timedelta(seconds=EXPORT_URL_EXPIRY_SECONDS)
        ).isoformat()

        # Audit event
        self.audit_repo.append(
            AuditEvent(
                event_id=new_uuid(),
                consultation_id=consultation_id,
                event_type=AuditAction.EXPORT_GENERATED,
                actor_id=auth_context.doctor_id,
                timestamp=utc_now_iso(),
                payload={"format": "pdf"},
            )
        )

        logger.info(
            "export_generated",
            extra=log_context(
                consultation_id=consultation_id,
                doctor_id=auth_context.doctor_id,
                format="pdf",
            ),
        )

        return ExportArtifact(
            consultation_id=consultation_id,
            format=ExportFormat.PDF,
            storage_key=s3_key,
            presigned_url=presigned_url,
            expires_at=expires_at,
        )
