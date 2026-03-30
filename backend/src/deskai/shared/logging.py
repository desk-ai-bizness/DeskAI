"""Logging helpers for safe structured logs."""

from aws_lambda_powertools import Logger

LOGGER = Logger(service="deskai-backend")


def get_logger() -> Logger:
    """Return the shared logger instance.

    Do not attach raw transcript content or patient-identifiable fields.
    """

    return LOGGER
