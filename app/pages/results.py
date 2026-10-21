"""Analysis results and report download page — guided dashboard layout."""

from __future__ import annotations

import logging

import streamlit as st

from app.components.analysis_view import render_analysis
from app.components.career_snapshot import render_career_snapshot, render_next_actions
from app.components.footer import render_footer
from app.session_state import (
    ANALYSIS_KEY,
    BROWSE_JOBS_KEY,
    CAREER_PROFILE_KEY,
    CORRELATION_ID_KEY,
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
from services.resume_quality_service import ResumeQualityService
from services.skill_development_service import SkillDevelopmentService

logger = logging.getLogger(__name__)


def render_results_page(
    report_service: ReportService,
    recommendation_service: RecommendationService,
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
        '<div class="section-eyebrow">Your personalised report</div>', unsafe_allow_html=True
    )
    st.header("Your resume review")
    st.caption("AI-generated career guidance — not a hiring decision.")

    # ── Job search filters ────────────────────────────────────────────────────
    with st.expander("Refine your job search", expanded=False):
        st.caption(
            "Optional filters narrow the job list; they do not resubmit your resume analysis."
        )
        role_column, location_column = st.columns(2)
        with role_column:
            role_input = st.text_input(
                "Target roles",
                value=", ".join(preferences.role_keywords),
                placeholder="e.g. software engineer, data analyst",
                max_chars=200,
                help="Separate role-title keywords with commas. Leave blank for any role.",
                key="job_role_filter_input",
            )
        with location_column:
            location_input = st.text_input(
                "Preferred location",
                value=preferences.location,
                placeholder="e.g. Bengaluru or India",
                max_chars=100,
                help="Searches listing locations. Leave blank for any location.",
                key="job_location_filter_input",
            )
        filter_col, refresh_col = st.columns([1, 1])
        with filter_col:
            if st.button("Apply job filters", type="primary"):
                preferences = JobSearchPreferences(
                    role_keywords=tuple(
                        keyword.strip()[:80] for keyword in role_input.split(",") if keyword.strip()
                    )[:8],
                    location=location_input.strip(),
                )
                st.session_state[JOB_SEARCH_PREFERENCES_KEY] = preferences
                _refresh_recommendation_state(
                    analysis,
                    recommendation_service,
                    preferences,
                    success_message="Job filters applied.",
                )
        with refresh_col:
            if st.button(
                "Refresh job recommendations",
                help="Recheck the current job catalog without resubmitting your resume.",
            ):
                correlation_id = new_correlation_id()
                st.session_state[CORRELATION_ID_KEY] = correlation_id
                _refresh_recommendation_state(
                    analysis,
                    recommendation_service,
                    preferences,
                    success_message="Job recommendations refreshed from the current catalog.",
                    correlation_id=correlation_id,
                )

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
    )

    render_footer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_empty_results() -> None:
    """Show a helpful empty state when no analysis has been run yet."""
    st.markdown('<div class="section-eyebrow">Results</div>', unsafe_allow_html=True)
    st.header("Your resume insights will appear here")
    st.markdown(
        "Start by uploading or pasting your resume on the **Analyze resume page**."
        "  Once the AI review is complete, your career insights, matched roles,"
        " skill-development plan, and downloadable report will appear here."
    )
    st.caption(
        "Your resume text is sent to the AI provider only after you give consent."
        "  Results are held in your active session and are not stored."
    )


def _refresh_recommendation_state(
    analysis: ResumeAnalysis,
    recommendation_service: RecommendationService,
    preferences: JobSearchPreferences,
    success_message: str,
    correlation_id: str | None = None,
) -> None:
    correlation_id = correlation_id or new_correlation_id()
    st.session_state[CORRELATION_ID_KEY] = correlation_id
    try:
        recommendations = recommendation_service.recommend(analysis, preferences=preferences)
        catalog_status = recommendation_service.catalog_status(preferences)
        browse_jobs = recommendation_service.current_jobs(limit=8, preferences=preferences)
        relevant_jobs = recommendation_service.current_jobs(limit=100, preferences=preferences)
    except ApplicationError as exc:
        st.session_state[RECOMMENDATION_ERROR_KEY] = exc.user_message
        st.session_state[JOB_CATALOG_STATUS_KEY] = None
        st.session_state[BROWSE_JOBS_KEY] = []
        resume_text = st.session_state.get(RESUME_TEXT_KEY, "")
        profile: CareerProfile = st.session_state.get(CAREER_PROFILE_KEY, CareerProfile())
        st.session_state[RESUME_QUALITY_KEY] = ResumeQualityService().evaluate(
            resume_text, career_stage=profile.stage
        )
        st.session_state[SKILL_DEVELOPMENT_PLAN_KEY] = []
        logger.warning(
            "Recommendation refresh failed correlation_id=%s error_code=%s",
            correlation_id,
            type(exc).__name__,
        )
        return

    st.session_state[RECOMMENDATIONS_KEY] = recommendations
    st.session_state[JOB_CATALOG_STATUS_KEY] = catalog_status
    st.session_state[BROWSE_JOBS_KEY] = browse_jobs
    resume_text = st.session_state.get(RESUME_TEXT_KEY, "")
    profile: CareerProfile = st.session_state.get(CAREER_PROFILE_KEY, CareerProfile())
    st.session_state[RESUME_QUALITY_KEY] = ResumeQualityService().evaluate(
        resume_text,
        relevant_jobs,
        career_stage=profile.stage,
    )
    st.session_state[SKILL_DEVELOPMENT_PLAN_KEY] = SkillDevelopmentService().build_plan(
        analysis, relevant_jobs, resume_text=resume_text
    )
    st.session_state[RECOMMENDATION_ERROR_KEY] = None
    st.success(success_message)
