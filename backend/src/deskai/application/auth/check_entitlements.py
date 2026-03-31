"""Check plan-based entitlements for a doctor."""

from dataclasses import dataclass

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.services import compute_entitlements
from deskai.domain.auth.value_objects import Entitlements
from deskai.ports.doctor_repository import DoctorRepository


@dataclass(frozen=True)
class CheckEntitlementsUseCase:
    """Compute current entitlements from plan rules and usage data."""

    doctor_repo: DoctorRepository

    def execute(self, profile: DoctorProfile) -> Entitlements:
        used = self.doctor_repo.count_consultations_this_month(
            profile.doctor_id
        )
        return compute_entitlements(
            plan_type=profile.plan_type,
            created_at=profile.created_at,
            consultations_used_this_month=used,
        )
