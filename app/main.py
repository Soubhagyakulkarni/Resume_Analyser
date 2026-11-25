"""Streamlit application composition root."""

# ruff: noqa: I001

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from app.components.footer import render_footer
from app.components.theme import apply_app_theme
from app.config.settings import Settings
from app.pages.analyze_resume import render_analyze_page
from app.pages.final_verdict import render_final_verdict_page
from app.pages.job_recommendations import render_job_recommendations_page
from app.pages.landing import render_about_page, render_home_page
from app.pages.login import render_login_page
from app.pages.results import render_results_page
from app.pages.resume_builder import render_resume_builder
from app.services.resume_service import ResumeService
from app.session_state import ANALYSIS_KEY, get_current_user
from app.utils.errors import ApplicationError
from app.utils.logging_config import configure_logging
from integrations.gemini_gateway import GeminiAnalysisGateway
from integrations.openai_gateway import OpenAIAnalysisGateway
from reports.pdf_renderer import ReportLabPdfRenderer
from repositories.supabase_job_repository import SupabaseJobRepository
from services.analysis_service import AnalysisService
from services.catalog_seeder import ensure_job_catalog
from services.recommendation_service import RecommendationService
from services.report_service import ReportService
from services.supabase_auth_service import SupabaseAuthService
from supabase import create_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ApplicationServices:
    resume: ResumeService
    analysis: AnalysisService | None
    recommendations: RecommendationService
    report: ReportService
    auth: SupabaseAuthService
    embedder: Callable[[str], list[float]] | None = None


@st.cache_resource
def _build_services() -> ApplicationServices:
    settings = Settings.from_environment()
    gateway = None
    if settings.ai_provider == "gemini":
        if settings.gemini_api_key:
            gateway = GeminiAnalysisGateway(settings)
    elif settings.openai_api_key:
        gateway = OpenAIAnalysisGateway(settings)
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise ValueError(
            "Create a Supabase project, run the documented SQL migration, and set "
            "SUPABASE_URL and SUPABASE_ANON_KEY."
        )
    if not settings.supabase_service_role_key:
        raise ValueError(
            "Set SUPABASE_SERVICE_ROLE_KEY as a server-side secret for the job catalog."
        )
    job_repository = SupabaseJobRepository(
        create_client(settings.supabase_url, settings.supabase_service_role_key)
    )
    ensure_job_catalog(job_repository, settings)
    ocr_extractor = getattr(gateway, "extract_text_from_pdf", None) if gateway is not None else None
    embedder = getattr(gateway, "embed_text", None) if gateway is not None else None
    return ApplicationServices(
        resume=ResumeService(
            settings.max_upload_bytes,
            settings.max_resume_chars,
            ocr_extractor=ocr_extractor,
        ),
        analysis=AnalysisService(gateway) if gateway is not None else None,
        recommendations=RecommendationService(
            job_repository, max_age_days=settings.job_listing_max_age_days
        ),
        report=ReportService(ReportLabPdfRenderer()),
        auth=SupabaseAuthService(settings.supabase_url, settings.supabase_anon_key),
        embedder=embedder,
    )


def _render_top_navigation(
    home_page: st.Page,
    about_page: st.Page,
    analyze_page: st.Page,
    job_recommendations_page: st.Page,
    resume_builder_page: st.Page,
) -> None:
    with st.container(key="top_navigation"):
        brand, home, about, analyze, jobs, builder, theme = st.columns(
            [1.1, 0.5, 0.7, 1.15, 1.45, 1.7, 0.8],
            gap="small",
        )
        with brand:
            st.markdown(
                """
                <div class="top-nav-brand">
                  <span class="top-nav-mark">R</span>
                  <span><strong>ResumeAI</strong><small>Career guidance</small></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with home:
            st.page_link(home_page, label="Home", width="stretch")
        with about:
            st.page_link(about_page, label="About Us", width="stretch")
        with analyze:
            st.page_link(analyze_page, label="Analyse Resume", width="stretch")
        with jobs:
            st.page_link(
                job_recommendations_page,
                label="Job Recommendation",
                width="stretch",
            )
        with builder:
            st.page_link(
                resume_builder_page,
                label="Build Your Own Resume",
                width="stretch",
            )
        with theme:
            st.toggle("Dark", key="dark_mode", help="Switch between light and dark themes.")


def main() -> None:
    st.set_page_config(
        page_title="ResumeAI | Career Tools",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False
    apply_app_theme(dark_mode=st.session_state["dark_mode"])
    try:
        settings = Settings.from_environment()
        configure_logging(settings.log_level)
    except (TypeError, ValueError):
        logger.exception("Invalid application configuration")
        st.error("The application configuration is invalid. Check the deployment settings.")
        return
    try:
        services = _build_services()
    except ValueError as exc:
        logger.error("Application configuration is incomplete: %s", exc)
        st.error(str(exc))
        return
    except (ApplicationError, OSError, RuntimeError):
        logger.exception("Application initialization failed")
        st.error("The application could not initialize. Check deployment configuration.")
        return

    current_user = get_current_user(st.session_state)

    def show_home_page() -> None:
        if services.analysis is None:
            key_name = "GEMINI_API_KEY" if settings.ai_provider == "gemini" else "OPENAI_API_KEY"
            st.warning(
                f"AI analysis is not configured. Set {key_name} in Streamlit Secrets "
                "(or your local .env file) to use resume analysis. The Resume builder works without an AI key."
            )
        render_home_page(analyze_page, resume_builder_page)

    def show_about_page() -> None:
        render_about_page()

    def show_analyze_page() -> None:
        if services.analysis is None:
            key_name = "GEMINI_API_KEY" if settings.ai_provider == "gemini" else "OPENAI_API_KEY"
            st.title("Analyse Resume")
            st.error(
                f"AI analysis is not configured. Set {key_name} in Streamlit Secrets "
                "(or your local .env file) to use resume analysis. The Resume builder works without an AI key."
            )
            render_footer()
            return
        render_analyze_page(
            services.resume,
            services.analysis,
            services.recommendations,
            settings.max_upload_bytes,
            settings.max_resume_chars,
        )
        if st.session_state.get(ANALYSIS_KEY) is not None:
            render_results_page(
                services.report,
                services.recommendations,
                embedder=services.embedder,
            )
        else:
            render_footer()

    def show_job_recommendations_page() -> None:
        render_job_recommendations_page(services.recommendations, analyze_page)

    def show_resume_builder_page() -> None:
        render_resume_builder(services.resume)

    def show_final_verdict_page() -> None:
        render_final_verdict_page(services.report, analyze_page)

    def show_login_page() -> None:
        render_login_page(services.auth)

    account_title = "Account" if current_user else "Sign in"
    analyze_page = st.Page(show_analyze_page, title="Analyse Resume")
    resume_builder_page = st.Page(show_resume_builder_page, title="Build Your Own Resume")
    home_page = st.Page(show_home_page, title="Home", default=True)
    about_page = st.Page(show_about_page, title="About Us")
    job_recommendations_page = st.Page(
        show_job_recommendations_page, title="Job Recommendation"
    )
    final_verdict_page = st.Page(show_final_verdict_page, title="Final Verdict")
    account_page = st.Page(show_login_page, title=account_title)
    navigation = st.navigation(
        [
            home_page,
            about_page,
            analyze_page,
            job_recommendations_page,
            resume_builder_page,
            final_verdict_page,
            account_page,
        ],
        position="hidden",
    )
    _render_top_navigation(
        home_page,
        about_page,
        analyze_page,
        job_recommendations_page,
        resume_builder_page,
    )
    navigation.run()


if __name__ == "__main__":
    main()
