from types import SimpleNamespace

import pytest

from services.supabase_auth_service import SupabaseAuthService


def _user():
    return SimpleNamespace(
        id="user-1",
        email="alex@example.com",
        user_metadata={"username": "alex_dev", "full_name": "Alex Developer"},
        created_at="2026-11-16T00:00:00Z",
        last_sign_in_at=None,
    )


def test_register_uses_supabase_auth_and_profile_metadata(monkeypatch):
    received = {}
    user = _user()

    class FakeAuth:
        def sign_up(self, credentials):
            received.update(credentials)
            return SimpleNamespace(user=user, session=object())

    client = SimpleNamespace(auth=FakeAuth())
    monkeypatch.setattr("services.supabase_auth_service.create_client", lambda *_: client)

    result, returned_client, error = SupabaseAuthService(
        "https://example.supabase.co", "anon"
    ).register("alex_dev", "Alex@Example.com", "Alex Developer", "SecurePass123!")

    assert error is None
    assert returned_client is client
    assert result is not None
    assert result.id == "user-1"
    assert result.username == "alex_dev"
    assert result.email == "alex@example.com"
    assert received["email"] == "alex@example.com"
    assert received["options"]["data"]["full_name"] == "Alex Developer"


def test_register_requires_email_confirmation_when_supabase_has_no_session(monkeypatch):
    class FakeAuth:
        def sign_up(self, _credentials):
            return SimpleNamespace(user=_user(), session=None)

    monkeypatch.setattr(
        "services.supabase_auth_service.create_client",
        lambda *_: SimpleNamespace(auth=FakeAuth()),
    )

    result = SupabaseAuthService("https://example.supabase.co", "anon").register(
        "alex_dev", "alex@example.com", "Alex Developer", "SecurePass123!"
    )

    assert result == (None, None, "Check your email to confirm your account, then sign in.")


def test_register_rejects_invalid_username_before_network_call(monkeypatch):
    monkeypatch.setattr(
        "services.supabase_auth_service.create_client",
        lambda *_: (_ for _ in ()).throw(AssertionError("should not connect")),
    )

    result = SupabaseAuthService("https://example.supabase.co", "anon").register(
        "bad username", "alex@example.com", "Alex Developer", "SecurePass123!"
    )

    assert result[0] is None
    assert result[1] is None
    assert "letters, numbers" in result[2]


def test_authenticate_and_sign_out_use_supabase_client(monkeypatch):
    user = _user()
    user.last_sign_in_at = "2026-11-16T01:00:00Z"
    calls = []

    class FakeAuth:
        def sign_in_with_password(self, credentials):
            calls.append(("sign_in", credentials))
            return SimpleNamespace(user=user)

        def sign_out(self):
            calls.append(("sign_out", None))

    client = SimpleNamespace(auth=FakeAuth())
    monkeypatch.setattr("services.supabase_auth_service.create_client", lambda *_: client)

    result, returned_client, error = SupabaseAuthService(
        "https://example.supabase.co", "anon"
    ).authenticate("Alex@Example.com", "SecurePass123!")

    assert error is None
    assert returned_client is client
    assert result is not None
    assert result.last_login_at == "2026-11-16T01:00:00Z"
    assert calls == [("sign_in", {"email": "alex@example.com", "password": "SecurePass123!"})]

    SupabaseAuthService.sign_out(client)
    assert calls[-1] == ("sign_out", None)


@pytest.mark.parametrize(
    ("exception_message", "expected_message"),
    [
        ("User already registered", "An account with this email already exists. Please sign in."),
        ("Email not confirmed", "Confirm your email address before signing in."),
        ("Invalid login credentials", "Invalid email or password."),
    ],
)
def test_auth_errors_are_mapped_to_user_messages(exception_message, expected_message):
    assert SupabaseAuthService._auth_error(ValueError(exception_message)) == expected_message


def test_verify_email_otp_success(monkeypatch):
    user = _user()
    received = {}

    class FakeAuth:
        def verify_otp(self, params):
            received.update(params)
            return SimpleNamespace(user=user)

    client = SimpleNamespace(auth=FakeAuth())
    monkeypatch.setattr("services.supabase_auth_service.create_client", lambda *_: client)

    auth = SupabaseAuthService("https://example.supabase.co", "anon")
    verified_user, verified_client, error = auth.verify_email_otp("Alex@Example.com", "123456")

    assert error is None
    assert verified_client is client
    assert verified_user is not None
    assert verified_user.email == "alex@example.com"
    assert received == {"email": "alex@example.com", "token": "123456", "type": "signup"}


def test_verify_email_otp_invalid_code(monkeypatch):
    class FakeAuth:
        def verify_otp(self, _params):
            raise ValueError("Token has expired or is invalid")

    client = SimpleNamespace(auth=FakeAuth())
    monkeypatch.setattr("services.supabase_auth_service.create_client", lambda *_: client)

    auth = SupabaseAuthService("https://example.supabase.co", "anon")
    user, _, error = auth.verify_email_otp("alex@example.com", "999999")

    assert user is None
    assert error is not None
    assert "Invalid or expired" in error


def test_resend_verification_code_success(monkeypatch):
    received = {}

    class FakeAuth:
        def resend(self, params):
            received.update(params)

    client = SimpleNamespace(auth=FakeAuth())
    monkeypatch.setattr("services.supabase_auth_service.create_client", lambda *_: client)

    auth = SupabaseAuthService("https://example.supabase.co", "anon")
    error = auth.resend_verification_code("Alex@Example.com")

    assert error is None
    assert received == {"type": "signup", "email": "alex@example.com"}


def test_send_password_reset_code_uses_normalized_email(monkeypatch):
    received = []

    class FakeAuth:
        def reset_password_for_email(self, email):
            received.append(email)

    client = SimpleNamespace(auth=FakeAuth())
    monkeypatch.setattr("services.supabase_auth_service.create_client", lambda *_: client)

    error = SupabaseAuthService(
        "https://example.supabase.co", "anon"
    ).send_password_reset_code("Alex@Example.com")

    assert error is None
    assert received == ["alex@example.com"]


def test_reset_password_with_code_verifies_recovery_before_updating(monkeypatch):
    calls = []

    class FakeAuth:
        def verify_otp(self, params):
            calls.append(("verify", params))
            return SimpleNamespace(user=_user(), session=object())

        def update_user(self, attributes):
            calls.append(("update", attributes))
            return SimpleNamespace(user=_user())

    client = SimpleNamespace(auth=FakeAuth())
    monkeypatch.setattr("services.supabase_auth_service.create_client", lambda *_: client)

    error = SupabaseAuthService(
        "https://example.supabase.co", "anon"
    ).reset_password_with_code("Alex@Example.com", "123456", "NewPass123!")

    assert error is None
    assert calls == [
        (
            "verify",
            {"email": "alex@example.com", "token": "123456", "type": "recovery"},
        ),
        ("update", {"password": "NewPass123!"}),
    ]


def test_reset_password_does_not_update_when_recovery_code_is_invalid(monkeypatch):
    class FakeAuth:
        def verify_otp(self, _params):
            return SimpleNamespace(user=None)

        def update_user(self, _attributes):
            raise AssertionError("password must not update without a verified code")

    monkeypatch.setattr(
        "services.supabase_auth_service.create_client",
        lambda *_: SimpleNamespace(auth=FakeAuth()),
    )

    error = SupabaseAuthService(
        "https://example.supabase.co", "anon"
    ).reset_password_with_code("alex@example.com", "000000", "NewPass123!")

    assert error is not None
    assert "Invalid or expired" in error


def test_reset_password_does_not_update_without_recovery_session(monkeypatch):
    class FakeAuth:
        def verify_otp(self, _params):
            return SimpleNamespace(user=_user(), session=None)

        def update_user(self, _attributes):
            raise AssertionError("password must not update without a recovery session")

    monkeypatch.setattr(
        "services.supabase_auth_service.create_client",
        lambda *_: SimpleNamespace(auth=FakeAuth()),
    )

    error = SupabaseAuthService(
        "https://example.supabase.co", "anon"
    ).reset_password_with_code("alex@example.com", "123456", "NewPass123!")

    assert error is not None
    assert "Invalid or expired" in error
