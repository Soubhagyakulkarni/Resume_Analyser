"""UI tests for the real login and registration page."""

from streamlit.testing.v1 import AppTest


def test_login_page_renders_unauthenticated_tabs(tmp_path):
    source = f"""
from pathlib import Path
import streamlit as st
from app.pages.login import render_login_page
from repositories.sqlite_user_repository import SQLiteUserRepository
from services.auth_service import AuthService

repo = SQLiteUserRepository(Path(r"{tmp_path}") / "users.sqlite3")
auth_service = AuthService(repo)
render_login_page(auth_service)
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


def test_register_and_login_flow(tmp_path):
    source = f"""
from pathlib import Path
import streamlit as st
from app.pages.login import render_login_page
from repositories.sqlite_user_repository import SQLiteUserRepository
from services.auth_service import AuthService

repo = SQLiteUserRepository(Path(r"{tmp_path}") / "users.sqlite3")
auth_service = AuthService(repo)
render_login_page(auth_service)
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

    # Verify session state has authenticated user
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


def test_logout_button_clears_session(tmp_path):
    source = f"""
from pathlib import Path
import streamlit as st
from app.pages.login import render_login_page
from models.user import AuthenticatedUser
from repositories.sqlite_user_repository import SQLiteUserRepository
from services.auth_service import AuthService

repo = SQLiteUserRepository(Path(r"{tmp_path}") / "users.sqlite3")
auth_service = AuthService(repo)

if "init_done" not in st.session_state:
    st.session_state["init_done"] = True
    st.session_state["authenticated_user"] = AuthenticatedUser(
        id="usr-mock",
        username="logged_in_user",
        email="logged@example.com",
        full_name="Logged User",
        created_at="2026-10-12T00:00:00Z",
    )

render_login_page(auth_service)
"""
    app = AppTest.from_string(source).run(timeout=10)
    assert not app.exception
    assert app.session_state["authenticated_user"].username == "logged_in_user"

    # Click the Sign Out button
    logout_btn = app.button(key="btn_logout")
    logout_btn.click().run(timeout=10)
    assert not app.exception
    assert "authenticated_user" not in app.session_state
