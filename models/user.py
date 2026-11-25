"""Typed domain models for user accounts and authentication."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Safe user profile for active session state without credentials."""

    id: str
    username: str
    email: str
    full_name: str
    created_at: str
    last_login_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize user data for logging or state checks without sensitive info."""
        return asdict(self)
