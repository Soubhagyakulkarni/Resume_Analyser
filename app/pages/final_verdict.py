"""Concise final assessment page."""

from __future__ import annotations

import logging

import streamlit as st

from app.components.career_snapshot import render_career_snapshot, render_next_actions
from app.components.footer import render_footer
from app.components.quality_checks_view import render_quality_checks
from app.session_state import (
    ANALYSIS_KEY,
    CAREER_PROFILE_KEY,
    RECOMMENDATIONS_KEY,
    RESUME_QUALITY_KEY,
    SKILL_DEVELOPMENT_PLAN_KEY,
)
from app.utils.errors import ApplicationError
from app.utils.identifiers import new_correlation_id
from models.analysis import ResumeAnalysis
from services.career_profile import CareerProfile
from services.report_service import ReportService
from services.resume_quality_service import ResumeQualityReport
from services.skill_development_service import SkillDevelopmentStep

logger = logging.getLogger(__name__)


def render_final_verdict_page(report_service: ReportService, analyze_page: st.Page) -> None:
    """Summarize an existing analysis and its recommended next actions."""
    st.markdown('<div class="section-eyebrow">Your assessment</div>', unsafe_allow_html=True)
    st.title("Final verdict")
    st.caption("A summary of the submitted resume—not an ATS score or hiring decision.")

    analysis: ResumeAnalysis | None = st.session_state.get(ANALYSIS_KEY)
    if analysis is None:
        st.info("Complete a resume analysis to see your final assessment.")
        st.page_link(analyze_page, label="Analyse resume")
        render_footer()
        return

    recommendations = st.session_state.get(RECOMMENDATIONS_KEY, [])
    skill_plan: list[SkillDevelopmentStep] = st.session_state.get(
        SKILL_DEVELOPMENT_PLAN_KEY, []
    )
    quality_report: ResumeQualityReport | None = st.session_state.get(RESUME_QUALITY_KEY)
    profile: CareerProfile = st.session_state.get(CAREER_PROFILE_KEY, CareerProfile())

    report_bytes = None
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
            "Final verdict report failed correlation_id=%s error_code=%s",
            correlation_id,
            type(exc).__name__,
        )
        st.error(f"{exc.user_message} Reference: {correlation_id}")

    render_career_snapshot(
        recommendations,
        skill_plan,
        quality_report,
        profile,
        report_ready=bool(report_bytes),
    )
    render_next_actions(analysis, recommendations, skill_plan, quality_report)

    with st.expander("Resume quality checks"):
        render_quality_checks(quality_report)

    if report_bytes:
        st.download_button(
            "Download analysis report",
            data=report_bytes,
            file_name="resume-analysis.pdf",
            mime="application/pdf",
            type="primary",
        )
    render_footer()
