"""Unit tests for AuthService registration and authentication workflows."""

import pytest

from models.user import AuthenticatedUser
from repositories.sqlite_user_repository import SQLiteUserRepository
from services.auth_service import AuthService


@pytest.fixture
def auth_service(tmp_path):
    repo = SQLiteUserRepository(tmp_path / "auth_test.sqlite3")
    return AuthService(repo)


def test_register_and_authenticate_by_username(auth_service):
    user, err = auth_service.register(
        username="john_doe",
        email="john@example.com",
        full_name="John Doe",
        password="MySecurePassword123!",
    )
    assert err is None
    assert isinstance(user, AuthenticatedUser)
    assert user.username == "john_doe"
    assert user.email == "john@example.com"
    assert user.full_name == "John Doe"

    # Authenticate using username
    logged_in, auth_err = auth_service.authenticate("john_doe", "MySecurePassword123!")
    assert auth_err is None
    assert logged_in is not None
    assert logged_in.username == "john_doe"
    assert logged_in.last_login_at is not None


def test_authenticate_by_email_case_insensitive(auth_service):
    auth_service.register(
        username="jane_dev",
        email="jane.dev@example.com",
        full_name="Jane Dev",
        password="PassWord456!",
    )

    # Login with uppercase email
    logged_in, err = auth_service.authenticate("JANE.DEV@EXAMPLE.COM", "PassWord456!")
    assert err is None
    assert logged_in is not None
    assert logged_in.email == "jane.dev@example.com"


def test_authenticate_with_wrong_password(auth_service):
    auth_service.register(
        username="alice",
        email="alice@example.com",
        full_name="Alice B",
        password="ValidPassword123",
    )

    logged_in, err = auth_service.authenticate("alice", "WrongPassword!")
    assert logged_in is None
    assert err == "Invalid username/email or password."


def test_authenticate_nonexistent_user(auth_service):
    logged_in, err = auth_service.authenticate("ghost_user", "AnyPassword123")
    assert logged_in is None
    assert err == "Invalid username/email or password."


def test_register_duplicate_username_and_email(auth_service):
    auth_service.register(
        username="unique_name",
        email="unique@example.com",
        full_name="Unique User",
        password="Password123!",
    )

    # Duplicate username
    user2, err2 = auth_service.register(
        username="unique_name",
        email="other@example.com",
        full_name="Other User",
        password="Password123!",
    )
    assert user2 is None
    assert "username already exists" in err2

    # Duplicate email
    user3, err3 = auth_service.register(
        username="another_name",
        email="unique@example.com",
        full_name="Another User",
        password="Password123!",
    )
    assert user3 is None
    assert "email address already exists" in err3


def test_register_validation_errors(auth_service):
    # Short password
    _, err = auth_service.register("valid_user", "u@example.com", "Name", "123")
    assert "at least 6 characters" in err

    # Invalid email
    _, err = auth_service.register("valid_user", "not-an-email", "Name", "Password123")
    assert "valid email" in err

    # Bad username
    _, err = auth_service.register("bad space", "u@example.com", "Name", "Password123")
    assert "letters, numbers" in err

    # Missing full name
    _, err = auth_service.register("valid_user", "u@example.com", "   ", "Password123")
    assert "full name" in err
