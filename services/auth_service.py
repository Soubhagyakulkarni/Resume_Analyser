"""Authentication service providing secure registration, password hashing, and login."""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
import uuid
from datetime import UTC, datetime

from app.utils.errors import UserAlreadyExistsError
from models.user import AuthenticatedUser, User
from services.ports import UserRepository

logger = logging.getLogger(__name__)

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Derive a cryptographic PBKDF2-HMAC-SHA256 password hash and salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return hash_bytes.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password in constant time to prevent timing attacks."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, password_hash)


def validate_username(username: str) -> str | None:
    """Validate username rules; return error message if invalid."""
    clean = username.strip()
    if len(clean) < 3:
        return "Username must be at least 3 characters long."
    if len(clean) > 50:
        return "Username cannot exceed 50 characters."
    if not USERNAME_REGEX.match(clean):
        return "Username can only contain letters, numbers, underscores, and hyphens."
    return None


def validate_email(email: str) -> str | None:
    """Validate email format; return error message if invalid."""
    clean = email.strip()
    if not clean or len(clean) > 254:
        return "Please enter a valid email address."
    if not EMAIL_REGEX.match(clean):
        return "Please enter a valid email address (e.g. user@example.com)."
    return None


def validate_password(password: str) -> str | None:
    """Validate password rules; return error message if invalid."""
    if len(password) < 6:
        return "Password must be at least 6 characters long."
    if len(password) > 128:
        return "Password is too long (maximum 128 characters)."
    return None


def validate_full_name(full_name: str) -> str | None:
    """Validate full name; return error message if invalid."""
    clean = full_name.strip()
    if not clean:
        return "Please enter your full name."
    if len(clean) > 100:
        return "Full name cannot exceed 100 characters."
    return None


class AuthService:
    """Coordinates user registration, password verification, and session state."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def register(
        self,
        username: str,
        email: str,
        full_name: str,
        password: str,
    ) -> tuple[AuthenticatedUser | None, str | None]:
        """Validate, hash, and persist a new user account.

        Returns:
            (AuthenticatedUser, None) on success.
            (None, error_message) on failure.
        """
        # Validate fields
        name_err = validate_full_name(full_name)
        if name_err:
            return None, name_err

        user_err = validate_username(username)
        if user_err:
            return None, user_err

        email_err = validate_email(email)
        if email_err:
            return None, email_err

        pass_err = validate_password(password)
        if pass_err:
            return None, pass_err

        clean_username = username.strip()
        clean_email = email.strip().lower()
        clean_name = full_name.strip()

        # Check existing username
        if self._repository.get_by_username(clean_username) is not None:
            return None, "An account with this username already exists. Please choose another."

        # Check existing email
        if self._repository.get_by_email(clean_email) is not None:
            return None, "An account with this email address already exists. Please sign in."

        # Hash password and create record
        pwd_hash, salt = hash_password(password)
        user_id = f"usr_{uuid.uuid4().hex[:16]}"
        now = datetime.now(UTC).isoformat()

        user = User(
            id=user_id,
            username=clean_username,
            email=clean_email,
            full_name=clean_name,
            password_hash=pwd_hash,
            salt=salt,
            created_at=now,
            last_login_at=now,
        )

        try:
            self._repository.create_user(user)
        except UserAlreadyExistsError:
            return None, "An account with this username or email already exists."

        logger.info(
            "Successfully registered user account id=%s username=%s", user_id, clean_username
        )
        return user.to_authenticated_user(), None

    def authenticate(
        self,
        identifier: str,
        password: str,
    ) -> tuple[AuthenticatedUser | None, str | None]:
        """Verify user credentials against persistent storage.

        Returns:
            (AuthenticatedUser, None) on success.
            (None, error_message) on failure.
        """
        clean_identifier = identifier.strip()
        if not clean_identifier or not password:
            return None, "Please enter both username/email and password."

        user = self._repository.get_by_identifier(clean_identifier)
        if user is None:
            return None, "Invalid username/email or password."

        if not verify_password(password, user.password_hash, user.salt):
            return None, "Invalid username/email or password."

        now = datetime.now(UTC).isoformat()
        try:
            self._repository.update_last_login(user.id, now)
        except Exception:  # noqa: BLE001
            logger.warning("Could not update last login timestamp for user_id=%s", user.id)

        auth_user = AuthenticatedUser(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            last_login_at=now,
        )
        logger.info("Successfully authenticated user id=%s username=%s", user.id, user.username)
        return auth_user, None

    def get_user(self, user_id: str) -> AuthenticatedUser | None:
        """Fetch user by ID."""
        user = self._repository.get_by_id(user_id)
        return user.to_authenticated_user() if user else None
