"""Analysis results and report download page — guided dashboard layout."""

from __future__ import annotations

import logging
from collections.abc import Callable

import streamlit as st

from app.components.analysis_view import render_analysis
from app.components.career_snapshot import render_career_snapshot, render_next_actions
from app.components.footer import render_footer
from app.session_state import (
    ANALYSIS_KEY,
    BROWSE_JOBS_KEY,
    CAREER_PROFILE_KEY,
    JOB_CATALOG_STATUS_KEY,
    JOB_SEARCH_PREFERENCES_KEY,
    RECOMMENDATION_ERROR_KEY,
    RECOMMENDATIONS_KEY,
    RESUME_QUALITY_KEY,
    RESUME_TEXT_KEY,
    SKILL_DEVELOPMENT_PLAN_KEY,
)
from app.utils.errors import ApplicationError
from app.utils.identifiers import new_correlation_id
from models.analysis import ResumeAnalysis
from services.career_profile import CareerProfile
from services.recommendation_service import JobSearchPreferences, RecommendationService
from services.report_service import ReportService

logger = logging.getLogger(__name__)


def render_results_page(
    report_service: ReportService,
    recommendation_service: RecommendationService,
    embedder: Callable[[str], list[float]] | None = None,
) -> None:
    analysis: ResumeAnalysis | None = st.session_state.get(ANALYSIS_KEY)
    recommendations = st.session_state.get(RECOMMENDATIONS_KEY, [])

    if analysis is None:
        _render_empty_results()
        render_footer()
        return

    preferences: JobSearchPreferences = st.session_state.get(
        JOB_SEARCH_PREFERENCES_KEY, JobSearchPreferences()
    )
    profile: CareerProfile = st.session_state.get(CAREER_PROFILE_KEY, CareerProfile())
    quality_report = st.session_state.get(RESUME_QUALITY_KEY)
    skill_plan = st.session_state.get(SKILL_DEVELOPMENT_PLAN_KEY, [])

    # ── Page header ──────────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-eyebrow">Your report</div>', unsafe_allow_html=True
    )
    st.header("Resume review")
    st.caption("AI-generated career guidance — not a hiring decision.")

    # ── Pre-generate report bytes (once per render) ───────────────────────────
    recommendations = st.session_state.get(RECOMMENDATIONS_KEY, [])
    quality_report = st.session_state.get(RESUME_QUALITY_KEY)
    skill_plan = st.session_state.get(SKILL_DEVELOPMENT_PLAN_KEY, [])
    report_bytes: bytes | None = None
    try:
        report_bytes = report_service.generate(
            analysis,
            recommendations,
            skill_plan,
            quality_report,
            career_profile=profile,
        )
    except ApplicationError as exc:
        correlation_id = new_correlation_id()
        logger.warning(
            "Report generation failed correlation_id=%s error_code=%s",
            correlation_id,
            type(exc).__name__,
        )
        st.error(f"{exc.user_message}  Reference: {correlation_id}")

    # Render the dashboard after filter application and report generation so
    # the snapshot reflects the exact listings and report state shown below.
    render_career_snapshot(
        recommendations,
        skill_plan,
        quality_report,
        profile,
        report_ready=bool(report_bytes),
    )
    render_next_actions(analysis, recommendations, skill_plan, quality_report)
    st.divider()

    # ── Recommendation error banner ───────────────────────────────────────────
    recommendation_error = st.session_state.get(RECOMMENDATION_ERROR_KEY)
    if recommendation_error:
        st.warning(recommendation_error)

    # ── Tabbed results ────────────────────────────────────────────────────────
    render_analysis(
        analysis,
        recommendations,
        st.session_state.get(JOB_CATALOG_STATUS_KEY),
        st.session_state.get(BROWSE_JOBS_KEY, []),
        preferences,
        quality_report,
        skill_plan,
        profile=profile,
        report_bytes=report_bytes,
        resume_text=st.session_state.get(RESUME_TEXT_KEY, ""),
        embedder=embedder,
    )

    render_footer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_empty_results() -> None:
    """Show a helpful empty state when no analysis has been run yet."""
    st.markdown('<div class="section-eyebrow">Results</div>', unsafe_allow_html=True)
    st.header("No results yet")
    st.markdown(
        "Analyze your resume to view feedback, job matches, a skills plan, and your report."
    )
    st.caption(
        "Resume text is sent to AI only after consent; results stay in your session, not the database."
    )
