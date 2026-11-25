"""Unit tests for registration input validation."""

from services.auth_validation import (
    validate_email,
    validate_full_name,
    validate_password,
    validate_username,
)


def test_validate_username():
    assert validate_username("john_doe") is None
    assert validate_username("jane-123") is None
    assert validate_username("ab") == "Username must be at least 3 characters long."
    assert (
        validate_username("bad space")
        == "Username can only contain letters, numbers, underscores, and hyphens."
    )
    assert (
        validate_username("bad@char")
        == "Username can only contain letters, numbers, underscores, and hyphens."
    )


def test_validate_email():
    assert validate_email("user@example.com") is None
    assert validate_email("user.name+tag@domain.co.in") is None
    assert (
        validate_email("invalid-email")
        == "Please enter a valid email address (e.g. user@example.com)."
    )
    assert validate_email("") == "Please enter a valid email address."


def test_validate_password():
    assert validate_password("valid_pwd") is None
    assert validate_password("12345") == "Password must be at least 6 characters long."


def test_validate_full_name():
    assert validate_full_name("Jane Doe") is None
    assert validate_full_name("") == "Please enter your full name."
    assert validate_full_name("   ") == "Please enter your full name."
