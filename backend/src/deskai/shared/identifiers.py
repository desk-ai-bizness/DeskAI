"""Identifier utilities."""

from uuid import uuid4


def new_uuid() -> str:
    """Generate a UUID4 string."""

    return str(uuid4())
