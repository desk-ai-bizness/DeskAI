"""Logging helpers for safe structured logs."""

from __future__ import annotations

from typing import Any

from aws_lambda_powertools import Logger

LOGGER = Logger(service="deskai-backend")


def get_logger() -> Logger:
    """Return the shared logger instance.

    Do not attach raw transcript content or patient-identifiable fields.
    """
    return LOGGER


def log_context(**kwargs: Any) -> dict[str, Any]:
    """Build an ``extra`` dict for structured log fields.

    Usage::

        logger.info("consultation_created", extra=log_context(
            consultation_id=c.consultation_id,
            doctor_id=auth.doctor_id,
            clinic_id=auth.clinic_id,
        ))

    Only non-None values are included.
    """
    return {k: v for k, v in kwargs.items() if v is not None}
