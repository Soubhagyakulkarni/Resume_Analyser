"""Input validation shared by the Supabase Auth workflow."""

import re

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_username(username: str) -> str | None:
    clean = username.strip()
    if len(clean) < 3:
        return "Username must be at least 3 characters long."
    if len(clean) > 50:
        return "Username cannot exceed 50 characters."
    if not USERNAME_REGEX.match(clean):
        return "Username can only contain letters, numbers, underscores, and hyphens."
    return None


def validate_email(email: str) -> str | None:
    clean = email.strip()
    if not clean or len(clean) > 254:
        return "Please enter a valid email address."
    if not EMAIL_REGEX.match(clean):
        return "Please enter a valid email address (e.g. user@example.com)."
    return None


def validate_password(password: str) -> str | None:
    if len(password) < 6:
        return "Password must be at least 6 characters long."
    if len(password) > 128:
        return "Password is too long (maximum 128 characters)."
    return None


def validate_full_name(full_name: str) -> str | None:
    clean = full_name.strip()
    if not clean:
        return "Please enter your full name."
    if len(clean) > 100:
        return "Full name cannot exceed 100 characters."
    return None
