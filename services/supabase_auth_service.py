"""Supabase Auth adapter for email/password accounts."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from supabase import Client, create_client
from supabase_auth.errors import AuthError

from models.user import AuthenticatedUser
from services.auth_validation import (
    validate_email,
    validate_full_name,
    validate_password,
    validate_username,
)

logger = logging.getLogger(__name__)


class SupabaseAuthService:
    def __init__(self, url: str, anon_key: str) -> None:
        self._url = url
        self._anon_key = anon_key

    def register(
        self,
        username: str,
        email: str,
        full_name: str,
        password: str,
    ) -> tuple[AuthenticatedUser | None, Client | None, str | None]:
        for error in (
            validate_full_name(full_name),
            validate_username(username),
            validate_email(email),
            validate_password(password),
        ):
            if error:
                return None, None, error
        try:
            client = create_client(self._url, self._anon_key)
            response = client.auth.sign_up(
                {
                    "email": email.strip().lower(),
                    "password": password,
                    "options": {
                        "data": {
                            "username": username.strip(),
                            "full_name": full_name.strip(),
                        }
                    },
                }
            )
            if response.session is None:
                return None, None, "Check your email to confirm your account, then sign in."
            return self._to_user(response.user), client, None
        except (AuthError, httpx.HTTPError, ValueError) as exc:
            logger.info("Supabase account registration failed: %s", type(exc).__name__)
            return None, None, self._auth_error(exc)

    def authenticate(
        self, email: str, password: str
    ) -> tuple[AuthenticatedUser | None, Client | None, str | None]:
        clean_email = email.strip().lower()
        if not clean_email or not password:
            return None, None, "Please enter both email and password."
        try:
            client = create_client(self._url, self._anon_key)
            response = client.auth.sign_in_with_password(
                {"email": clean_email, "password": password}
            )
            return self._to_user(response.user), client, None
        except (AuthError, httpx.HTTPError, ValueError) as exc:
            logger.info("Supabase sign-in failed: %s", type(exc).__name__)
            return None, None, self._auth_error(exc)

    def verify_email_otp(
        self, email: str, token: str
    ) -> tuple[AuthenticatedUser | None, Client | None, str | None]:
        """Verify the 6-digit confirmation code sent to user email."""
        clean_email = email.strip().lower()
        clean_token = token.strip()
        if not clean_email or not clean_token:
            return None, None, "Please enter both email and verification code."
        try:
            client = create_client(self._url, self._anon_key)
            response = client.auth.verify_otp(
                {"email": clean_email, "token": clean_token, "type": "signup"}
            )
            if response.user is None:
                return None, None, "Verification code is invalid or has expired."
            return self._to_user(response.user), client, None
        except (AuthError, httpx.HTTPError, ValueError) as exc:
            logger.info("Supabase OTP verification failed: %s", type(exc).__name__)
            msg = str(exc).lower()
            if "expired" in msg or "invalid" in msg or "token" in msg:
                return None, None, "Invalid or expired verification code. Please check your email or request a new one."
            return None, None, self._auth_error(exc)

    def resend_verification_code(self, email: str) -> str | None:
        """Resend a new 6-digit verification code to the user's email."""
        clean_email = email.strip().lower()
        if not clean_email:
            return "Please enter a valid email address."
        try:
            client = create_client(self._url, self._anon_key)
            client.auth.resend({"type": "signup", "email": clean_email})
            return None
        except (AuthError, httpx.HTTPError, ValueError) as exc:
            logger.info("Supabase resend OTP failed: %s", type(exc).__name__)
            return self._auth_error(exc)

    def send_password_reset_code(self, email: str) -> str | None:
        """Send a password recovery email containing Supabase's configured OTP."""
        email_error = validate_email(email)
        if email_error:
            return email_error
        try:
            client = create_client(self._url, self._anon_key)
            client.auth.reset_password_for_email(email.strip().lower())
            return None
        except (AuthError, httpx.HTTPError, ValueError) as exc:
            logger.info("Supabase password reset request failed: %s", type(exc).__name__)
            return self._auth_error(exc)

    def reset_password_with_code(
        self, email: str, token: str, new_password: str
    ) -> str | None:
        """Verify a recovery OTP and set a new password for that account."""
        email_error = validate_email(email)
        if email_error:
            return email_error
        password_error = validate_password(new_password)
        if password_error:
            return password_error
        clean_token = token.strip()
        if not clean_token:
            return "Please enter the verification code sent to your email."
        try:
            client = create_client(self._url, self._anon_key)
            response = client.auth.verify_otp(
                {
                    "email": email.strip().lower(),
                    "token": clean_token,
                    "type": "recovery",
                }
            )
            if response.user is None or response.session is None:
                return "Invalid or expired verification code. Request a new one and try again."
            updated_user = client.auth.update_user({"password": new_password}).user
            if updated_user is None:
                return "Password could not be updated. Please request a new recovery code."
            return None
        except (AuthError, httpx.HTTPError, ValueError) as exc:
            logger.info("Supabase password reset failed: %s", type(exc).__name__)
            message = str(exc).lower()
            if "expired" in message or "invalid" in message or "token" in message:
                return "Invalid or expired verification code. Request a new one and try again."
            return self._auth_error(exc)

    @staticmethod
    def sign_out(client: Client | None) -> None:
        if client is not None:
            try:
                client.auth.sign_out()
            except (AuthError, httpx.HTTPError):
                logger.exception("Supabase sign-out failed")
                raise

    @staticmethod
    def _to_user(user: Any) -> AuthenticatedUser:
        metadata = user.user_metadata or {}
        email = user.email or ""
        username = metadata.get("username") or email.partition("@")[0]
        full_name = metadata.get("full_name") or username
        created_at = user.created_at or datetime.now(UTC).isoformat()
        return AuthenticatedUser(
            id=str(user.id),
            username=username,
            email=email,
            full_name=full_name,
            created_at=created_at,
            last_login_at=getattr(user, "last_sign_in_at", None),
        )

    @staticmethod
    def _auth_error(exc: AuthError | httpx.HTTPError | ValueError) -> str:
        message = str(exc).lower()
        if "already registered" in message or "already been registered" in message:
            return "An account with this email already exists. Please sign in."
        if "invalid login credentials" in message:
            return "Invalid email or password."
        if "email not confirmed" in message:
            return "Confirm your email address before signing in."
        if "password" in message and ("weak" in message or "least" in message):
            return "Choose a stronger password and try again."
        return "Supabase authentication is unavailable. Check the project settings and try again."
