"""Focused job recommendation page."""

from __future__ import annotations

import logging

import streamlit as st

from app.components.footer import render_footer
from app.components.job_cards import render_job_recommendations
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
from services.resume_quality_service import ResumeQualityService
from services.skill_development_service import SkillDevelopmentService

logger = logging.getLogger(__name__)


def render_job_recommendations_page(
    recommendation_service: RecommendationService, analyze_page: st.Page
) -> None:
    """Render current role matches and controls for refining them."""
    st.markdown('<div class="section-eyebrow">Explore opportunities</div>', unsafe_allow_html=True)
    st.title("Job recommendations")
    st.write("Current roles with skills that overlap your resume.")

    analysis: ResumeAnalysis | None = st.session_state.get(ANALYSIS_KEY)
    if analysis is None:
        st.info("Analyse your resume first to see job matches.")
        st.page_link(analyze_page, label="Analyse resume")
        render_footer()
        return

    preferences: JobSearchPreferences = st.session_state.get(
        JOB_SEARCH_PREFERENCES_KEY, JobSearchPreferences()
    )
    with st.expander("Refine your search", expanded=False):
        role_column, location_column = st.columns(2)
        with role_column:
            role_input = st.text_input(
                "Target roles",
                value=", ".join(preferences.role_keywords),
                placeholder="e.g. software engineer, data analyst",
                max_chars=200,
                key="recommendation_role_filter_input",
            )
        with location_column:
            location_input = st.text_input(
                "Preferred location",
                value=preferences.location,
                placeholder="e.g. Bengaluru or India",
                max_chars=100,
                key="recommendation_location_filter_input",
            )
        apply_column, refresh_column = st.columns(2)
        with apply_column:
            if st.button("Apply filters", type="primary", key="apply_recommendation_filters"):
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
                    "Job recommendations updated.",
                )
        with refresh_column:
            if st.button(
                "Refresh listings",
                help="Check the current job catalog without resubmitting your resume.",
                key="refresh_recommendation_listings",
            ):
                _refresh_recommendation_state(
                    analysis,
                    recommendation_service,
                    preferences,
                    "Job listings refreshed.",
                    correlation_id=new_correlation_id(),
                )

    error = st.session_state.get(RECOMMENDATION_ERROR_KEY)
    if error:
        st.warning(error)
    render_job_recommendations(
        st.session_state.get(RECOMMENDATIONS_KEY, []),
        st.session_state.get(JOB_CATALOG_STATUS_KEY),
        st.session_state.get(BROWSE_JOBS_KEY, []),
        preferences,
    )
    render_footer()


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
        from app.config.settings import Settings
        from services.catalog_seeder import ensure_job_catalog

        search_query = preferences.role_keywords[0] if preferences.role_keywords else None
        ensure_job_catalog(
            recommendation_service._repository,
            Settings.from_environment(),
            force_refresh=True,
            search_query=search_query,
            location_query=preferences.location or None,
        )
        recommendations = recommendation_service.recommend(analysis, preferences=preferences)
        catalog_status = recommendation_service.catalog_status(preferences)
        browse_jobs = recommendation_service.current_jobs(limit=8, preferences=preferences)
        relevant_jobs = recommendation_service.current_jobs(limit=100, preferences=preferences)
    except ApplicationError as exc:
        st.session_state[RECOMMENDATION_ERROR_KEY] = exc.user_message
        st.session_state[JOB_CATALOG_STATUS_KEY] = None
        st.session_state[BROWSE_JOBS_KEY] = []
        profile: CareerProfile = st.session_state.get(CAREER_PROFILE_KEY, CareerProfile())
        st.session_state[RESUME_QUALITY_KEY] = ResumeQualityService().evaluate(
            st.session_state.get(RESUME_TEXT_KEY, ""), career_stage=profile.stage
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
    profile = st.session_state.get(CAREER_PROFILE_KEY, CareerProfile())
    resume_text = st.session_state.get(RESUME_TEXT_KEY, "")
    st.session_state[RESUME_QUALITY_KEY] = ResumeQualityService().evaluate(
        resume_text, relevant_jobs, career_stage=profile.stage
    )
    st.session_state[SKILL_DEVELOPMENT_PLAN_KEY] = SkillDevelopmentService().build_plan(
        analysis, relevant_jobs, resume_text=resume_text
    )
    st.session_state[RECOMMENDATION_ERROR_KEY] = None
    st.success(success_message)
