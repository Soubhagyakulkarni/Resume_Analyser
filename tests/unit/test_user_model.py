"""Unit tests for models.user domain entities."""

from models.user import AuthenticatedUser, User


def test_user_creation_and_credential_hiding():
    user = User(
        id="usr-123",
        username="alex",
        email="alex@example.com",
        full_name="Alex Smith",
        password_hash="mock-hash",
        salt="mock-salt",
        created_at="2026-10-12T00:00:00Z",
        last_login_at="2026-10-12T01:00:00Z",
    )

    assert user.id == "usr-123"
    assert user.username == "alex"
    assert user.email == "alex@example.com"
    assert user.password_hash == "mock-hash"
    assert user.salt == "mock-salt"

    auth_user = user.to_authenticated_user()
    assert isinstance(auth_user, AuthenticatedUser)
    assert auth_user.id == "usr-123"
    assert auth_user.username == "alex"
    assert auth_user.email == "alex@example.com"
    assert auth_user.full_name == "Alex Smith"
    assert auth_user.created_at == "2026-10-12T00:00:00Z"
    assert auth_user.last_login_at == "2026-10-12T01:00:00Z"

    # Ensure sensitive credentials are not on the authenticated user
    assert not hasattr(auth_user, "password_hash")
    assert not hasattr(auth_user, "salt")


def test_authenticated_user_to_dict():
    auth_user = AuthenticatedUser(
        id="usr-456",
        username="sam",
        email="sam@example.com",
        full_name="Sam Taylor",
        created_at="2026-10-12T02:00:00Z",
    )
    user_dict = auth_user.to_dict()
    assert user_dict == {
        "id": "usr-456",
        "username": "sam",
        "email": "sam@example.com",
        "full_name": "Sam Taylor",
        "created_at": "2026-10-12T02:00:00Z",
        "last_login_at": None,
    }
