"""Authentication page providing real user login and account creation."""

from __future__ import annotations

import logging
from datetime import datetime
from html import escape

import streamlit as st

from app.components.footer import render_footer
from app.session_state import (
    SUPABASE_AUTH_CLIENT_KEY,
    get_current_user,
    logout_user,
    set_current_user,
)
from models.user import AuthenticatedUser
from services.supabase_auth_service import SupabaseAuthService

logger = logging.getLogger(__name__)


def render_login_page(auth_service: SupabaseAuthService) -> None:
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
        _render_authenticated_dashboard(current_user, auth_service)
    else:
        _render_auth_forms(auth_service)

    render_footer()


def _render_authenticated_dashboard(
    current_user: AuthenticatedUser, auth_service: SupabaseAuthService
) -> None:
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
                auth_client = st.session_state.get(SUPABASE_AUTH_CLIENT_KEY)
                logout_user(st.session_state)
                auth_service.sign_out(auth_client)
                st.success("You have been signed out.")
                st.rerun()


def _render_otp_verification(auth_service: SupabaseAuthService) -> None:
    """Render the 6-digit email confirmation code entry screen."""
    email = str(st.session_state.get("pending_verification_email", ""))
    st.markdown('<div class="section-eyebrow">Email verification</div>', unsafe_allow_html=True)
    st.header("Check your inbox")
    st.caption(
        f"A 6-digit verification code was sent to **{escape(email)}** by Supabase Auth."
    )

    with st.container(border=True):
        st.markdown("#### Enter verification code")
        st.caption("Enter the code from your email to activate your account and complete sign-in.")

        with st.form("form_verify_otp", clear_on_submit=False):
            token = st.text_input(
                "Verification code",
                placeholder="e.g. 123456",
                max_chars=12,
                key="otp_token_input",
                help="Check your spam or junk folder if the email does not appear in your inbox.",
            )
            submit_verify = st.form_submit_button(
                "Verify & Sign In  →",
                type="primary",
                use_container_width=True,
            )

        if submit_verify:
            if not token.strip():
                st.error("Please enter the verification code sent to your email.")
            elif hasattr(auth_service, "verify_email_otp"):
                user, client, err = auth_service.verify_email_otp(email, token.strip())
                if err:
                    st.error(err)
                elif user:
                    st.session_state.pop("pending_verification_email", None)
                    st.session_state[SUPABASE_AUTH_CLIENT_KEY] = client
                    set_current_user(st.session_state, user)
                    st.success(f"Email verified! Welcome, {user.full_name or user.username}!")
                    st.rerun()

        col_resend, col_cancel = st.columns(2)
        with col_resend:
            if (
                st.button("Resend code", key="btn_resend_otp", use_container_width=True)
                and hasattr(auth_service, "resend_verification_code")
            ):
                err = auth_service.resend_verification_code(email)
                if err:
                    st.error(err)
                else:
                    st.success("A new verification code has been sent to your email.")
        with col_cancel:
            if st.button("Use different email / Back", key="btn_cancel_otp", use_container_width=True):
                st.session_state.pop("pending_verification_email", None)
                st.rerun()


def _render_auth_forms(auth_service: SupabaseAuthService) -> None:
    """Show Sign In and Create Account tabs with validation and database storage."""
    if st.session_state.get("pending_verification_email"):
        _render_otp_verification(auth_service)
        return

    st.markdown(
        '<div class="section-eyebrow">Account access</div>',
        unsafe_allow_html=True,
    )
    st.header("Sign in or create an account")
    st.caption(
        "Create an optional account for email/password sign-in. Resume analysis remains"
        " available to guests."
    )

    tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

    # ── Tab 1: Sign In ─────────────────────────────────────────────────────────
    with tab_signin, st.container(border=True):
        st.markdown("#### Welcome back")
        st.caption("Enter your email and password to access your account.")

        with st.form("form_signin", clear_on_submit=False):
            identifier = st.text_input(
                "Email address",
                placeholder="jane@example.com",
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
                st.error("Please enter both your email address and password.")
            else:
                user, auth_client, err = auth_service.authenticate(identifier, password)
                if err:
                    st.error(err)
                    st.info(
                        "Don't have an account yet? Switch to the **Create Account** tab above."
                    )
                elif user:
                    st.session_state[SUPABASE_AUTH_CLIENT_KEY] = auth_client
                    set_current_user(st.session_state, user)
                    st.success(f"Welcome back, {user.full_name or user.username}!")
                    st.rerun()

        st.caption("Passwords and email confirmation are managed by Supabase Auth.")

    # ── Tab 2: Create Account ──────────────────────────────────────────────────
    with tab_register, st.container(border=True):
        st.markdown("#### Create your free account")
        st.caption(
            "Create an account to sign in with your email and password."
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
                new_user, auth_client, err = auth_service.register(
                    username, email, full_name, pwd
                )
                if err:
                    if "confirm your account" in err.lower() or "check your email" in err.lower():
                        st.session_state["pending_verification_email"] = email.strip().lower()
                        st.rerun()
                    else:
                        st.error(err)
                elif new_user:
                    st.session_state[SUPABASE_AUTH_CLIENT_KEY] = auth_client
                    set_current_user(st.session_state, new_user)
                    st.success(
                        f"Account created successfully! Welcome to Career Advisor, {new_user.full_name}."
                    )
                    st.rerun()

        st.caption(
            "Your account is managed by Supabase Auth. We store only your display name and username "
            "in your Supabase Auth profile; passwords are never stored by this app. Check your email "
            "to confirm a new account before signing in."
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
