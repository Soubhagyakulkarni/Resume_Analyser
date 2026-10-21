"""Streamlit application composition root."""

# ruff: noqa: I001

import logging
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from app.components.theme import apply_app_theme
from app.config.settings import Settings
from app.pages.analyze_resume import render_analyze_page
from app.pages.login import render_login_page
from app.pages.results import render_results_page
from app.pages.resume_builder import render_resume_builder
from app.services.resume_service import ResumeService
from app.session_state import get_current_user, logout_user
from app.utils.errors import ApplicationError
from app.utils.logging_config import configure_logging
from integrations.gemini_gateway import GeminiAnalysisGateway
from integrations.openai_gateway import OpenAIAnalysisGateway
from reports.pdf_renderer import ReportLabPdfRenderer
from repositories.sqlite_job_repository import SQLiteJobRepository
from repositories.sqlite_user_repository import SQLiteUserRepository
from services.analysis_service import AnalysisService
from services.auth_service import AuthService
from services.recommendation_service import RecommendationService
from services.report_service import ReportService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ApplicationServices:
    resume: ResumeService
    analysis: AnalysisService | None
    recommendations: RecommendationService
    report: ReportService
    auth: AuthService


@st.cache_resource
def _build_services() -> ApplicationServices:
    settings = Settings.from_environment()
    gateway = None
    if settings.ai_provider == "gemini":
        if settings.gemini_api_key:
            gateway = GeminiAnalysisGateway(settings)
    elif settings.openai_api_key:
        gateway = OpenAIAnalysisGateway(settings)
    job_repository = SQLiteJobRepository(settings.sqlite_database_path)
    user_repository = SQLiteUserRepository(settings.sqlite_user_database_path)
    return ApplicationServices(
        resume=ResumeService(settings.max_upload_bytes, settings.max_resume_chars),
        analysis=AnalysisService(gateway) if gateway is not None else None,
        recommendations=RecommendationService(
            job_repository, max_age_days=settings.job_listing_max_age_days
        ),
        report=ReportService(ReportLabPdfRenderer()),
        auth=AuthService(user_repository),
    )


def _extract_initials(name: str) -> str:
    """Extract 1-2 letter uppercase initials from full name or username."""
    parts = [p for p in name.strip().split() if p]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    if parts and parts[0]:
        return parts[0][:2].upper()
    return "U"


def _render_sidebar_brand() -> None:
    """Render top brand identity in the sidebar."""
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="sidebar-brand-prism">R</div>
          <div class="sidebar-brand-info">
            <div class="sidebar-brand-name">ResumeAI</div>
            <div class="sidebar-brand-tag">Career guidance</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar_auth(current_user: object | None) -> None:
    """Show concise account status above the primary navigation."""
    _render_sidebar_brand()
    st.markdown('<div class="section-eyebrow">Account</div>', unsafe_allow_html=True)
    if current_user is not None:
        raw_name = getattr(current_user, "full_name", "") or getattr(
            current_user, "username", "User"
        )
        raw_username = getattr(current_user, "username", "")
        name = escape(raw_name)
        username = escape(raw_username)
        initials = escape(_extract_initials(raw_name))
        st.markdown(
            f"""
            <div class="sidebar-user-card">
              <div class="sidebar-user-header">
                <div class="sidebar-user-avatar">{initials}</div>
                <div class="sidebar-user-meta">
                  <div class="sidebar-user-name">{name}</div>
                  <div class="sidebar-user-handle">@{username}</div>
                </div>
              </div>
              <div class="sidebar-status-pill">
                <span class="status-dot"></span> Active Session
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sign Out", key="sidebar_signout", use_container_width=True):
            logout_user(st.session_state)
            st.rerun()
    else:
        st.markdown(
            """
            <div class="sidebar-guest-card">
              <div class="sidebar-guest-badge">Guest session</div>
              <div class="sidebar-guest-text">
                Resume analysis is held in this browser session.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(page_title="AI Resume Analyzer", layout="wide")
    apply_app_theme()
    try:
        settings = Settings.from_environment()
        configure_logging(settings.log_level)
    except (TypeError, ValueError):
        logger.exception("Invalid application configuration")
        st.error("The application configuration is invalid. Check the deployment settings.")
        return
    try:
        services = _build_services()
    except (ApplicationError, OSError, ValueError, RuntimeError):
        logger.exception("Application initialization failed")
        st.error("The application could not initialize. Check deployment configuration.")
        return

    current_user = get_current_user(st.session_state)

    def show_analyze_page() -> None:
        if services.analysis is None:
            key_name = "GEMINI_API_KEY" if settings.ai_provider == "gemini" else "OPENAI_API_KEY"
            st.title("Analyze resume")
            st.error(
                f"AI analysis is not configured. Set {key_name} in your local .env file "
                "to use resume analysis. The Resume builder works without an AI key."
            )
            return
        render_analyze_page(
            services.resume,
            services.analysis,
            services.recommendations,
            settings.max_upload_bytes,
            settings.max_resume_chars,
        )

    def show_results_page() -> None:
        render_results_page(services.report, services.recommendations)

    def show_resume_builder_page() -> None:
        render_resume_builder(services.resume)

    def show_login_page() -> None:
        render_login_page(services.auth)

    account_title = "Account" if current_user else "Sign in / Register"
    analyze_page = st.Page(show_analyze_page, title="Analyze resume", default=True)
    results_page = st.Page(show_results_page, title="Results")
    resume_builder_page = st.Page(show_resume_builder_page, title="Resume builder")
    account_page = st.Page(show_login_page, title=account_title)
    navigation = st.navigation(
        [analyze_page, results_page, resume_builder_page, account_page],
        position="hidden",
    )

    with st.sidebar:
        _render_sidebar_auth(current_user)
        st.markdown('<div class="section-eyebrow">Workspace</div>', unsafe_allow_html=True)
        st.page_link(analyze_page, label="Analyze resume", use_container_width=True)
        st.page_link(results_page, label="Results", use_container_width=True)
        st.page_link(resume_builder_page, label="Resume builder", use_container_width=True)
        st.page_link(account_page, label=account_title, use_container_width=True)

    navigation.run()


if __name__ == "__main__":
    main()
