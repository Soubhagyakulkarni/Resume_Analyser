"""Integration tests for SQLiteUserRepository with persistent database files."""

import pytest

from app.utils.errors import UserAlreadyExistsError
from models.user import User
from repositories.sqlite_user_repository import SQLiteUserRepository


@pytest.fixture
def user_repo(tmp_path):
    db_file = tmp_path / "test_users.sqlite3"
    assert not db_file.exists()
    repo = SQLiteUserRepository(db_file)
    assert db_file.exists()  # Automatically creates database file if not present
    return repo


def test_create_and_fetch_user(user_repo):
    user = User(
        id="usr-1",
        username="alex",
        email="alex@example.com",
        full_name="Alex Turner",
        password_hash="mock-hash-1",
        salt="mock-salt-1",
        created_at="2026-10-12T10:00:00Z",
    )

    user_repo.create_user(user)

    fetched = user_repo.get_by_id("usr-1")
    assert fetched is not None
    assert fetched.username == "alex"
    assert fetched.email == "alex@example.com"
    assert fetched.full_name == "Alex Turner"
    assert fetched.password_hash == "mock-hash-1"
    assert fetched.salt == "mock-salt-1"


def test_case_insensitive_lookups(user_repo):
    user = User(
        id="usr-2",
        username="JohnDoe",
        email="John.Doe@Example.com",
        full_name="John Doe",
        password_hash="mock-hash-2",
        salt="mock-salt-2",
        created_at="2026-10-12T10:00:00Z",
    )
    user_repo.create_user(user)

    # By username
    assert user_repo.get_by_username("johndoe") is not None
    assert user_repo.get_by_username("JOHNDOE") is not None

    # By email
    assert user_repo.get_by_email("john.doe@example.com") is not None
    assert user_repo.get_by_email("JOHN.DOE@EXAMPLE.COM") is not None

    # By identifier
    assert user_repo.get_by_identifier("johndoe") is not None
    assert user_repo.get_by_identifier("john.doe@example.com") is not None


def test_reject_duplicate_username_or_email(user_repo):
    user1 = User(
        id="usr-3",
        username="unique_user",
        email="first@example.com",
        full_name="User One",
        password_hash="hash1",
        salt="salt1",
        created_at="2026-10-12T10:00:00Z",
    )
    user_repo.create_user(user1)

    # Duplicate username
    dup_username = User(
        id="usr-4",
        username="UNIQUE_USER",
        email="other@example.com",
        full_name="User Two",
        password_hash="hash2",
        salt="salt2",
        created_at="2026-10-12T10:00:00Z",
    )
    with pytest.raises(UserAlreadyExistsError):
        user_repo.create_user(dup_username)

    # Duplicate email
    dup_email = User(
        id="usr-5",
        username="different_user",
        email="FIRST@example.com",
        full_name="User Three",
        password_hash="hash3",
        salt="salt3",
        created_at="2026-10-12T10:00:00Z",
    )
    with pytest.raises(UserAlreadyExistsError):
        user_repo.create_user(dup_email)


def test_update_last_login_and_count(user_repo):
    assert user_repo.count_users() == 0

    user = User(
        id="usr-6",
        username="sarah",
        email="sarah@example.com",
        full_name="Sarah Connor",
        password_hash="hash",
        salt="salt",
        created_at="2026-10-12T10:00:00Z",
        last_login_at=None,
    )
    user_repo.create_user(user)
    assert user_repo.count_users() == 1

    user_repo.update_last_login("usr-6", "2026-10-12T12:00:00Z")
    updated = user_repo.get_by_id("usr-6")
    assert updated.last_login_at == "2026-10-12T12:00:00Z"
