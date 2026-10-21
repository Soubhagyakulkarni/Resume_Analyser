"""Authentication page providing real user login and account creation."""

from __future__ import annotations

import logging
from datetime import datetime

import streamlit as st

from app.components.footer import render_footer
from app.session_state import get_current_user, logout_user, set_current_user
from models.user import AuthenticatedUser
from services.auth_service import AuthService

logger = logging.getLogger(__name__)


def render_login_page(auth_service: AuthService) -> None:
    """Render the real user authentication dashboard (Sign In / Create Account)."""
    current_user = get_current_user(st.session_state)

    st.markdown(
        """
        <div class="app-brand">
          <span class="app-brand-mark">R</span> Career clarity, one resume at a time
        </div>
        """,
        unsafe_allow_html=True,
    )

    if current_user is not None:
        _render_authenticated_dashboard(current_user)
    else:
        _render_auth_forms(auth_service)

    render_footer()


def _render_authenticated_dashboard(current_user: AuthenticatedUser) -> None:
    """Show user profile, session details, and logout option when signed in."""
    st.markdown(
        '<div class="section-eyebrow">User account</div>',
        unsafe_allow_html=True,
    )
    st.header(f"Welcome, {current_user.full_name or current_user.username}")
    st.caption("You are currently signed in to your AI Career & Resume Analyzer account.")

    name_str = current_user.full_name or current_user.username
    parts = [p for p in name_str.strip().split() if p]
    initials = (
        f"{parts[0][0]}{parts[-1][0]}".upper()
        if len(parts) >= 2
        else (parts[0][:2].upper() if parts else "U")
    )

    with st.container(border=True):
        col_avatar, col_info = st.columns([1, 4])
        with col_avatar:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; align-items: center; padding: 0.8rem 0;">
                  <div style="width: 74px; height: 74px; border-radius: 50%; background: #eeeeFA; display: grid; place-items: center; color: #4646b8; font-weight: 700; font-size: 1.7rem; border: 1px solid #dadaf1;">
                    {initials}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_info:
            st.markdown(f"### {current_user.full_name}")
            st.markdown(f"**Username:** `@{current_user.username}`")
            st.markdown(f"**Email address:** `{current_user.email}`")

            # Format timestamps safely
            created_str = _format_iso(current_user.created_at)
            last_login_str = _format_iso(current_user.last_login_at)
            st.caption(f"Member since: {created_str}  ·  Last login: {last_login_str}")

        st.divider()

        col_nav, col_logout = st.columns([3, 1])
        with col_nav:
            st.info(
                "Your account is active. Use the **Analyze resume** page to upload"
                " or paste a resume for career guidance and job recommendations."
            )
        with col_logout:
            if st.button("Sign Out", type="secondary", use_container_width=True, key="btn_logout"):
                logout_user(st.session_state)
                st.success("You have been signed out.")
                st.rerun()


def _render_auth_forms(auth_service: AuthService) -> None:
    """Show Sign In and Create Account tabs with validation and database storage."""
    st.markdown(
        '<div class="section-eyebrow">Account access</div>',
        unsafe_allow_html=True,
    )
    st.header("Sign in or create an account")
    st.caption(
        "Sign in to personalize your career recommendations, or create a free account"
        " if you are a new user."
    )

    tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

    # ── Tab 1: Sign In ─────────────────────────────────────────────────────────
    with tab_signin, st.container(border=True):
        st.markdown("#### Welcome back")
        st.caption("Enter your email or username and password to access your account.")

        with st.form("form_signin", clear_on_submit=False):
            identifier = st.text_input(
                "Email or Username",
                placeholder="e.g. janedoe or jane@example.com",
                key="login_ident",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_pwd",
            )
            submit_signin = st.form_submit_button(
                "Sign In  →",
                type="primary",
                use_container_width=True,
            )

        if submit_signin:
            if not identifier.strip() or not password:
                st.error("Please enter both your username/email and password.")
            else:
                user, err = auth_service.authenticate(identifier, password)
                if err:
                    st.error(err)
                    st.info(
                        "Don't have an account yet? Switch to the **Create Account** tab above."
                    )
                elif user:
                    set_current_user(st.session_state, user)
                    st.success(f"Welcome back, {user.full_name or user.username}!")
                    st.rerun()

        st.caption("Passwords are cryptographically verified using PBKDF2-HMAC-SHA256.")

    # ── Tab 2: Create Account ──────────────────────────────────────────────────
    with tab_register, st.container(border=True):
        st.markdown("#### Create your free account")
        st.caption(
            "New user? Register below to save your career preferences,"
            " track skill goals, and get tailored resume guidance."
        )

        with st.form("form_register", clear_on_submit=False):
            full_name = st.text_input(
                "Full Name",
                placeholder="e.g. Jane Doe",
                key="reg_name",
                help="Your full display name.",
            )
            col_u, col_e = st.columns(2)
            with col_u:
                username = st.text_input(
                    "Username",
                    placeholder="e.g. janedoe",
                    key="reg_user",
                    help="3-50 alphanumeric characters, underscores, or hyphens.",
                )
            with col_e:
                email = st.text_input(
                    "Email Address",
                    placeholder="e.g. jane@example.com",
                    key="reg_mail",
                    help="A valid email address for account identification.",
                )

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                pwd = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 6 characters",
                    key="reg_pwd1",
                )
            with col_p2:
                pwd_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter password",
                    key="reg_pwd2",
                )

            agree_terms = st.checkbox(
                "I understand this service provides career guidance, not hiring guarantees.",
                value=True,
                key="reg_terms",
            )

            submit_register = st.form_submit_button(
                "Create Account  →",
                type="primary",
                use_container_width=True,
            )

        if submit_register:
            if not agree_terms:
                st.error("Please confirm the service terms to create an account.")
            elif pwd != pwd_confirm:
                st.error("Passwords do not match. Please re-enter your password.")
            else:
                new_user, err = auth_service.register(username, email, full_name, pwd)
                if err:
                    st.error(err)
                elif new_user:
                    set_current_user(st.session_state, new_user)
                    st.success(
                        f"Account created successfully! Welcome to Career Advisor, {new_user.full_name}."
                    )
                    st.rerun()

        st.caption(
            "Your user data is stored in the local SQLite database. "
            "Passwords are securely hashed with a unique per-user cryptographic salt."
        )


def _format_iso(iso_str: str | None) -> str:
    """Format an ISO 8601 string to a friendly readable date."""
    if not iso_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y at %H:%M UTC")
    except (ValueError, TypeError):
        return iso_str
