"""Time utility helpers."""

from datetime import UTC, datetime


def utc_now_iso() -> str:
    """Return the current timestamp in ISO 8601 format."""

    return datetime.now(tz=UTC).isoformat()
