"""Typed domain models for user accounts and authentication."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class User:
    """Persistent user entity stored in the database."""

    id: str
    username: str
    email: str
    full_name: str
    password_hash: str
    salt: str
    created_at: str
    last_login_at: str | None = None

    def to_authenticated_user(self) -> AuthenticatedUser:
        """Convert to a safe representation that excludes password credentials."""
        return AuthenticatedUser(
            id=self.id,
            username=self.username,
            email=self.email,
            full_name=self.full_name,
            created_at=self.created_at,
            last_login_at=self.last_login_at,
        )


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
