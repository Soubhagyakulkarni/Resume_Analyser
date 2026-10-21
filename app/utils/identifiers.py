"""Opaque request identifiers for privacy-safe operational correlation."""

from uuid import uuid4


def new_correlation_id() -> str:
    """Generate a random identifier without embedding user data."""
    return uuid4().hex
