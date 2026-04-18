"""CPF normalization, validation, and masking helpers."""

import re

from deskai.domain.patient.exceptions import PatientValidationError

_CPF_LENGTH = 11


def normalize_cpf(value: str | None) -> str:
    """Return a digits-only CPF after validating its checksum."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != _CPF_LENGTH:
        raise PatientValidationError("CPF is required and must contain 11 digits.")
    if len(set(digits)) == 1:
        raise PatientValidationError("CPF is invalid.")
    if not _has_valid_checksum(digits):
        raise PatientValidationError("CPF is invalid.")
    return digits


def mask_cpf(value: str | None) -> str:
    """Return a masked CPF suitable for UI display."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != _CPF_LENGTH:
        return ""
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def cpf_search_digits(value: str | None) -> str:
    """Return CPF search digits without requiring a complete CPF."""
    return re.sub(r"\D", "", value or "")


def _has_valid_checksum(digits: str) -> bool:
    first = _calculate_digit(digits[:9], start_weight=10)
    second = _calculate_digit(digits[:9] + str(first), start_weight=11)
    return digits[-2:] == f"{first}{second}"


def _calculate_digit(base_digits: str, *, start_weight: int) -> int:
    total = sum(
        int(digit) * weight
        for digit, weight in zip(base_digits, range(start_weight, 1, -1), strict=True)
    )
    remainder = (total * 10) % 11
    return 0 if remainder == 10 else remainder
