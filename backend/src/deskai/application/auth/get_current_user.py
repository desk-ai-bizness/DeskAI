"""Resolve the authenticated doctor profile."""

from dataclasses import dataclass

from deskai.domain.auth.entities import DoctorProfile
from deskai.domain.auth.exceptions import DoctorProfileNotFoundError
from deskai.ports.doctor_repository import DoctorRepository


@dataclass(frozen=True)
class GetCurrentUserUseCase:
    """Look up the doctor profile for a Cognito user."""

    doctor_repo: DoctorRepository

    def execute(self, identity_provider_id: str) -> DoctorProfile:
        profile = self.doctor_repo.find_by_identity_provider_id(identity_provider_id)
        if profile is None:
            raise DoctorProfileNotFoundError(
                f"No doctor profile found for user '{identity_provider_id}'."
            )
        return profile
