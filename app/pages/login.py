"""Authentication page providing real user login and account creation."""

from __future__ import annotations

import logging
from datetime import datetime
from html import escape

import streamlit as st

from app.components.footer import render_footer
from app.session_state import (
    PASSWORD_RESET_EMAIL_KEY,
    PASSWORD_RESET_REQUEST_KEY,
    PASSWORD_RESET_SUCCESS_KEY,
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
                  <div style="width: 74px; height: 74px; border-radius: 50%; background: var(--color-periwinkle); display: grid; place-items: center; color: var(--color-monday-violet); font-weight: 700; font-size: 1.7rem; border: 1px solid var(--color-mist);">
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

            created_str = _format_iso(current_user.created_at)
            st.caption(f"Member since {created_str}")

        st.divider()
        if st.button("Sign out", type="secondary", key="btn_logout"):
            auth_client = st.session_state.get(SUPABASE_AUTH_CLIENT_KEY)
            logout_user(st.session_state)
            auth_service.sign_out(auth_client)
            st.success("You have been signed out.")
            st.rerun()


def _render_otp_verification(auth_service: SupabaseAuthService) -> None:
    """Render the 6-digit email confirmation code entry screen."""
    email = str(st.session_state.get("pending_verification_email", ""))
    st.markdown('<div class="section-eyebrow">Email verification</div>', unsafe_allow_html=True)
    st.header("Verify your email")
    st.caption(f"Enter the 6-digit code sent to **{escape(email)}**.")

    with st.container(border=True):
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
    if st.session_state.get(PASSWORD_RESET_EMAIL_KEY):
        _render_password_reset_code(auth_service)
        return
    if st.session_state.get(PASSWORD_RESET_REQUEST_KEY):
        _render_password_reset_request(auth_service)
        return
    if st.session_state.pop(PASSWORD_RESET_SUCCESS_KEY, False):
        st.success("Your password was updated. Sign in with your new password.")

    st.markdown(
        '<div class="section-eyebrow">Account access</div>',
        unsafe_allow_html=True,
    )
    st.header("Sign in")
    st.caption("Optional — resume analysis is available without an account.")

    tab_signin, tab_register = st.tabs(["Sign In", "Create Account"])

    # ── Tab 1: Sign In ─────────────────────────────────────────────────────────
    with tab_signin, st.container(border=True):
        st.markdown("#### Welcome back")

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

        if st.button("Forgot password?", key="btn_forgot_password"):
            st.session_state[PASSWORD_RESET_REQUEST_KEY] = True
            st.rerun()

    # ── Tab 2: Create Account ──────────────────────────────────────────────────
    with tab_register, st.container(border=True):
        st.markdown("#### Create account")

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
                    st.success(f"Account created. Welcome, {new_user.full_name}.")
                    st.rerun()

        st.caption(
            "Supabase manages passwords and email verification; this app stores only your display name "
            "and username in your profile."
        )


def _render_password_reset_request(auth_service: SupabaseAuthService) -> None:
    st.markdown('<div class="section-eyebrow">Account recovery</div>', unsafe_allow_html=True)
    st.header("Reset your password")
    st.caption("Enter your email to request a recovery code.")
    with st.container(border=True):
        with st.form("form_password_reset_request", clear_on_submit=False):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("login_ident", ""),
                placeholder="jane@example.com",
                key="password_reset_email_input",
            )
            submit = st.form_submit_button(
                "Send verification code",
                type="primary",
                use_container_width=True,
                key="submit_password_reset_request",
            )
        if submit:
            error = auth_service.send_password_reset_code(email)
            if error:
                st.error(error)
            else:
                st.session_state[PASSWORD_RESET_EMAIL_KEY] = email.strip().lower()
                st.session_state.pop(PASSWORD_RESET_REQUEST_KEY, None)
                st.rerun()
    st.caption("If an account exists for that email, a recovery code will be sent.")
    if st.button("Back to sign in", key="btn_back_from_reset_request"):
        st.session_state.pop(PASSWORD_RESET_REQUEST_KEY, None)
        st.rerun()


def _render_password_reset_code(auth_service: SupabaseAuthService) -> None:
    email = str(st.session_state[PASSWORD_RESET_EMAIL_KEY])
    st.markdown('<div class="section-eyebrow">Account recovery</div>', unsafe_allow_html=True)
    st.header("Check your inbox")
    st.caption(f"Enter the recovery code sent to **{escape(email)}**.")
    with st.container(border=True):
        with st.form("form_password_reset_code", clear_on_submit=False):
            token = st.text_input(
                "Verification code",
                placeholder="Enter the code from your email",
                max_chars=12,
                key="password_reset_token",
            )
            new_password = st.text_input(
                "New password",
                type="password",
                placeholder="At least 6 characters",
                key="password_reset_new_password",
            )
            confirm_password = st.text_input(
                "Confirm new password",
                type="password",
                key="password_reset_confirm_password",
            )
            submit = st.form_submit_button(
                "Update password",
                type="primary",
                use_container_width=True,
                key="submit_password_reset_update",
            )
        if submit:
            if not token.strip():
                st.error("Please enter the verification code sent to your email.")
            elif new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                error = auth_service.reset_password_with_code(email, token, new_password)
                if error:
                    st.error(error)
                else:
                    st.session_state.pop(PASSWORD_RESET_EMAIL_KEY, None)
                    st.session_state[PASSWORD_RESET_SUCCESS_KEY] = True
                    st.rerun()

    resend, back = st.columns(2)
    with resend:
        if st.button("Resend code", key="btn_resend_password_reset"):
            error = auth_service.send_password_reset_code(email)
            if error:
                st.error(error)
            else:
                st.success("If an account exists for that email, a new code was sent.")
    with back:
        if st.button("Back to sign in", key="btn_back_from_reset_code"):
            st.session_state.pop(PASSWORD_RESET_EMAIL_KEY, None)
            st.rerun()


def _format_iso(iso_str: str | None) -> str:
    """Format an ISO 8601 string to a friendly readable date."""
    if not iso_str:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%b %d, %Y at %H:%M UTC")
    except (ValueError, TypeError):
        return iso_str
