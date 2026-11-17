"""UI tests for the real login and registration page."""

from streamlit.testing.v1 import AppTest


def test_login_page_renders_unauthenticated_tabs():
    source = """
import streamlit as st
from app.pages.login import render_login_page
from models.user import AuthenticatedUser

class FakeAuth:
    def register(self, username, email, full_name, password):
        return AuthenticatedUser("usr-1", username, email, full_name, "now"), object(), None

    def authenticate(self, email, password):
        return AuthenticatedUser("usr-1", "alex_dev", email, "Alex Developer", "now"), object(), None

    def sign_out(self, client):
        pass

render_login_page(FakeAuth())
"""
    app = AppTest.from_string(source).run(timeout=10)
    assert not app.exception

    # Should display headers
    headers = [item.value for item in app.header]
    assert any("Sign in or create an account" in h for h in headers)
    markdowns = "\n".join(item.value for item in app.markdown)
    assert "Welcome back" in markdowns
    assert "Create your free account" in markdowns

    # Buttons for both Sign In and Create Account should exist
    button_labels = [b.label for b in app.button]
    assert any("Sign In" in b for b in button_labels)
    assert any("Create Account" in b for b in button_labels)


def test_register_and_login_flow():
    source = """
import streamlit as st
from app.pages.login import render_login_page
from models.user import AuthenticatedUser

class FakeAuth:
    def register(self, username, email, full_name, password):
        return AuthenticatedUser("usr-1", username, email, full_name, "now"), object(), None

    def authenticate(self, email, password):
        return AuthenticatedUser("usr-1", "alex_dev", email, "Alex Developer", "now"), object(), None

    def sign_out(self, client):
        pass

render_login_page(FakeAuth())
"""
    app = AppTest.from_string(source).run(timeout=10)
    assert not app.exception

    # Register form inputs: reg_name, reg_user, reg_mail, reg_pwd1, reg_pwd2
    app.text_input(key="reg_name").set_value("Alex Developer")
    app.text_input(key="reg_user").set_value("alex_dev")
    app.text_input(key="reg_mail").set_value("alex@example.com")
    app.text_input(key="reg_pwd1").set_value("SecurePass123!")
    app.text_input(key="reg_pwd2").set_value("SecurePass123!")

    # Submit registration form using the Create Account submit button
    create_btn = next(b for b in app.button if "Create Account" in b.label)
    create_btn.click().run(timeout=10)
    assert not app.exception

    auth_user = app.session_state["authenticated_user"]
    assert auth_user is not None
    assert auth_user.username == "alex_dev"
    assert auth_user.email == "alex@example.com"
    assert auth_user.full_name == "Alex Developer"

    # Now verify that when re-rendered with authenticated user, dashboard shows
    headers = [item.value for item in app.header]
    assert any("Welcome, Alex Developer" in h for h in headers)
    markdowns = "\n".join(item.value for item in app.markdown)
    assert "@alex_dev" in markdowns
    assert "alex@example.com" in markdowns


def test_email_confirmation_code_completes_registration():
    source = """
import streamlit as st
from app.pages.login import render_login_page
from models.user import AuthenticatedUser

class FakeAuth:
    def register(self, username, email, full_name, password):
        return None, None, "Check your email to confirm your account, then sign in."

    def authenticate(self, email, password):
        return None, None, "Not used"

    def verify_email_otp(self, email, token):
        assert email == "alex@example.com"
        assert token == "123456"
        return AuthenticatedUser("usr-1", "alex_dev", email, "Alex Developer", "now"), object(), None

    def resend_verification_code(self, email):
        return None

    def sign_out(self, client):
        pass

render_login_page(FakeAuth())
"""
    app = AppTest.from_string(source).run(timeout=10)
    assert not app.exception

    app.text_input(key="reg_name").set_value("Alex Developer")
    app.text_input(key="reg_user").set_value("alex_dev")
    app.text_input(key="reg_mail").set_value("alex@example.com")
    app.text_input(key="reg_pwd1").set_value("SecurePass123!")
    app.text_input(key="reg_pwd2").set_value("SecurePass123!")
    next(b for b in app.button if "Create Account" in b.label).click().run(timeout=10)

    assert not app.exception
    assert app.session_state["pending_verification_email"] == "alex@example.com"
    assert any("Check your inbox" in item.value for item in app.header)

    app.text_input(key="otp_token_input").set_value("123456")
    next(b for b in app.button if "Verify & Sign In" in b.label).click().run(timeout=10)

    assert not app.exception
    assert "pending_verification_email" not in app.session_state
    assert app.session_state["authenticated_user"].email == "alex@example.com"


def test_logout_button_clears_session():
    source = """
import streamlit as st
from app.pages.login import render_login_page
from models.user import AuthenticatedUser

class FakeAuth:
    def register(self, username, email, full_name, password):
        return None, None, "Not used"

    def authenticate(self, email, password):
        return None, None, "Not used"

    def sign_out(self, client):
        pass

if "init_done" not in st.session_state:
    st.session_state["init_done"] = True
    st.session_state["authenticated_user"] = AuthenticatedUser(
        id="usr-mock",
        username="logged_in_user",
        email="logged@example.com",
        full_name="Logged User",
        created_at="2026-10-12T00:00:00Z",
    )

render_login_page(FakeAuth())
"""
    app = AppTest.from_string(source).run(timeout=10)
    assert not app.exception
    assert app.session_state["authenticated_user"].username == "logged_in_user"

    # Click the Sign Out button
    logout_btn = app.button(key="btn_logout")
    logout_btn.click().run(timeout=10)
    assert not app.exception
    assert "authenticated_user" not in app.session_state
