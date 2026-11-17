"""Unit tests for password hashing and validation functions."""

from services.auth_service import (
    hash_password,
    validate_email,
    validate_full_name,
    validate_password,
    validate_username,
    verify_password,
)


def test_password_hash_and_verify():
    raw_password = "SecretPassword123!"
    pwd_hash, salt = hash_password(raw_password)

    assert pwd_hash
    assert salt
    assert len(salt) == 32  # 16 bytes hex

    assert verify_password(raw_password, pwd_hash, salt) is True
    assert verify_password("WrongPassword!", pwd_hash, salt) is False


def test_unique_salts_generate_distinct_hashes():
    password = "SamePassword"
    hash1, salt1 = hash_password(password)
    hash2, salt2 = hash_password(password)

    assert salt1 != salt2
    assert hash1 != hash2
    assert verify_password(password, hash1, salt1) is True
    assert verify_password(password, hash2, salt2) is True


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
