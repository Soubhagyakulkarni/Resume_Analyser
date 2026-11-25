"""Unit tests for models.user domain entities."""

from models.user import AuthenticatedUser


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
