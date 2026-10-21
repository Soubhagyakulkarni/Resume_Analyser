"""Career snapshot row (metric cards) and "Your next 3 actions" panel."""

from __future__ import annotations

import streamlit as st

from models.analysis import ResumeAnalysis
from models.job import JobRecommendation
from services.career_profile import (
    CareerProfile,
    NextAction,
    calculate_readiness,
    generate_next_actions,
)
from services.resume_quality_service import ResumeQualityReport
from services.skill_development_service import SkillDevelopmentStep


def render_career_snapshot(
    recommendations: list[JobRecommendation],
    skill_plan: list[SkillDevelopmentStep],
    quality_report: ResumeQualityReport | None,
    profile: CareerProfile | None,
    report_ready: bool,
) -> None:
    """Render the top Career Snapshot metric-card row on the results page."""
    readiness = calculate_readiness(quality_report)
    highest_priority_skills = sum(step.listing_count >= 3 for step in skill_plan)

    st.markdown('<div class="section-eyebrow">Career Snapshot</div>', unsafe_allow_html=True)
    if profile and profile.is_set and profile.emphasis_note():
        st.caption(profile.emphasis_note())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Resume Readiness",
            value=readiness,
            help=(
                "Derived from Resume Quality Checks only. Not an ATS score or hiring prediction."
            ),
        )
    with col2:
        st.metric(
            label="Relevant Roles Found",
            value=str(len(recommendations)),
            help="Number of current listings with at least one matched skill.",
        )
    with col3:
        st.metric(
            label="Priority Skills",
            value=str(highest_priority_skills),
            help=("Skills in the Start now tier, appearing in at least three selected listings."),
        )
    with col4:
        st.metric(
            label="Report Status",
            value="Ready" if report_ready else "Unavailable",
            help=(
                "Your PDF report is ready to download from the Download Report tab."
                if report_ready
                else "Report generation failed. Your resume insights remain available."
            ),
        )


def render_next_actions(
    analysis: ResumeAnalysis,
    recommendations: list[JobRecommendation],
    skill_plan: list[SkillDevelopmentStep],
    quality_report: ResumeQualityReport | None,
) -> None:
    """Render the 'Your next 3 actions' panel below the snapshot."""
    actions = generate_next_actions(analysis, recommendations, skill_plan, quality_report)
    if not actions:
        return

    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">Action plan</div>', unsafe_allow_html=True)
        st.markdown("#### Your next 3 actions")
        st.caption(
            "These are derived from your analysis results."
            "  Click the section links in each tab to explore details."
        )
        for action in actions:
            _render_action_card(action)


def _render_action_card(action: NextAction) -> None:
    badge_style = (
        "background: var(--color-apricot-soft); color: #c2410c; border: 1px solid #fed7aa;"
        if action.priority == "High"
        else "background: var(--color-sky-soft); color: #0369a1; border: 1px solid #bae6fd;"
        if action.priority == "Medium"
        else "background: var(--color-mint-soft); color: #15803d; border: 1px solid #bbf7d0;"
    )
    st.markdown(
        f"""
        <div style="background: #ffffff; border: 1px solid var(--color-mist); border-radius: 16px; padding: 1rem 1.25rem; margin-bottom: 0.85rem; box-shadow: 0 2px 12px rgba(0,0,0,0.03);">
          <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.4rem;">
            <span style="font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em; {badge_style}">
              {action.priority} priority
            </span>
            <span style="font-weight: 600; font-size: 0.98rem; color: var(--color-ink);">
              {action.title}
            </span>
          </div>
          <div style="color: var(--color-slate); font-size: 0.88rem; line-height: 1.5; margin-bottom: 0.45rem;">
            {action.explanation}
          </div>
          <div style="font-size: 0.8rem; font-weight: 600; color: var(--color-monday-violet); text-transform: uppercase; letter-spacing: 0.04em;">
            → {action.section}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
