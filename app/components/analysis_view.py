"""Tabbed presentation of validated analysis and recommendations."""

from __future__ import annotations

from html import escape

import streamlit as st

from app.components.jd_match_view import render_jd_match_tab
from app.components.job_cards import render_job_recommendations
from app.components.quality_checks_view import render_quality_checks
from app.components.skill_plan_view import render_skill_plan
from models.analysis import ResumeAnalysis, Skill
from models.job import Job, JobRecommendation
from services.career_profile import CareerProfile, sort_job_recommendations
from services.recommendation_service import JobCatalogStatus, JobSearchPreferences
from services.resume_quality_service import ResumeQualityReport
from services.skill_development_service import SkillDevelopmentStep


def render_analysis(
    analysis: ResumeAnalysis,
    recommendations: list[JobRecommendation],
    catalog_status: JobCatalogStatus | None = None,
    browse_jobs: list[Job] | None = None,
    preferences: JobSearchPreferences | None = None,
    quality_report: ResumeQualityReport | None = None,
    skill_plan: list[SkillDevelopmentStep] | None = None,
    profile: CareerProfile | None = None,
    report_bytes: bytes | None = None,
    resume_text: str = "",
) -> None:
    """Render detailed results in six tabs below the Career Snapshot."""
    tab_insights, tab_jd, tab_jobs, tab_skills, tab_checks, tab_report = st.tabs(
        [
            "Resume Insights",
            "🎯 JD Match & Skills",
            "Job Recommendations",
            "Skill Development Plan",
            "Resume Quality Checks",
            "Download Report",
        ]
    )

    with tab_insights:
        _render_insights_tab(analysis, profile)

    with tab_jd:
        render_jd_match_tab(analysis, resume_text)

    with tab_jobs:
        _render_jobs_tab(recommendations, catalog_status, browse_jobs, preferences)

    with tab_skills:
        render_skill_plan(skill_plan or [])

    with tab_checks:
        render_quality_checks(quality_report)

    with tab_report:
        _render_report_tab(report_bytes)


# ---------------------------------------------------------------------------
# Tab: Resume Insights
# ---------------------------------------------------------------------------


def _render_insights_tab(analysis: ResumeAnalysis, profile: CareerProfile | None) -> None:
    # Summary
    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">The short version</div>', unsafe_allow_html=True)
        st.subheader("Your resume, at a glance")
        st.write(analysis.summary)

    # Strengths (from experience highlights)
    if analysis.experience_highlights:
        with st.container(border=True):
            st.markdown(
                '<div class="section-eyebrow">Resume strengths</div>', unsafe_allow_html=True
            )
            st.subheader("What your resume shows well")
            for highlight in analysis.experience_highlights:
                st.markdown(f"- {highlight}")

    # Skills grid
    st.subheader("Skills & experience")
    skills_col, exp_col = st.columns([1, 1], gap="large")
    with skills_col, st.container(border=True):
        st.markdown('<div class="section-eyebrow">What you bring</div>', unsafe_allow_html=True)
        st.markdown("#### Technical skills")
        _render_skills(analysis.technical_skills, label="Technical")
        st.markdown("#### People skills")
        _render_skills(analysis.soft_skills, label="People")

    with exp_col, st.container(border=True):
        st.markdown('<div class="section-eyebrow">Your experience</div>', unsafe_allow_html=True)
        st.write(analysis.experience_assessment)

    # Improvement suggestions as an actionable checklist
    if analysis.suggestions:
        with st.container(border=True):
            st.markdown(
                '<div class="section-eyebrow">Make your resume stronger</div>',
                unsafe_allow_html=True,
            )
            st.subheader("Improvement checklist")
            st.caption(
                "These suggestions are based on the resume text provided.  Only add"
                " information that is truthful and accurate."
            )
            for suggestion in analysis.suggestions:
                with st.expander(
                    f"{suggestion.priority.title()} priority — {suggestion.issue}",
                    expanded=suggestion.priority.lower() == "high",
                ):
                    st.write(suggestion.recommendation)
                    if suggestion.evidence:
                        st.caption(f"Evidence from resume: {suggestion.evidence}")
                    else:
                        st.caption(
                            "Not enough information in the resume to cite specific evidence."
                        )

    # Learning suggestions
    if analysis.learning_suggestions:
        with st.container(border=True):
            st.markdown('<div class="section-eyebrow">Keep building</div>', unsafe_allow_html=True)
            st.subheader("Learning directions from AI analysis")
            for suggestion in analysis.learning_suggestions:
                st.markdown(f"- {suggestion}")

    # Caveats / limitations
    if analysis.caveats:
        with st.expander("About these results and their limitations"):
            for caveat in analysis.caveats:
                st.markdown(f"- {caveat}")

    st.caption(
        "Skill gaps mean a requirement was not found in the submitted resume;"
        " they do not mean you do not have that skill."
    )


def _render_skills(skills: tuple[Skill, ...], label: str = "") -> None:
    if not skills:
        st.caption("No skills could be confidently identified.")
        return
    chips = " ".join(f'<span class="skill-chip">{escape(skill.name)}</span>' for skill in skills)
    st.markdown(chips, unsafe_allow_html=True)
    with st.expander("Review evidence"):
        for skill in skills:
            confidence = (
                "Partial evidence"
                if skill.inferred
                else "Clear evidence"
                if skill.evidence
                else "Evidence unavailable"
            )
            evidence_text = skill.evidence or "Not enough information in the resume."
            st.markdown(f"**{skill.name}** · {confidence}")
            st.caption(evidence_text)


# ---------------------------------------------------------------------------
# Tab: Job Recommendations
# ---------------------------------------------------------------------------


def _render_jobs_tab(
    recommendations: list[JobRecommendation],
    catalog_status: JobCatalogStatus | None,
    browse_jobs: list[Job] | None,
    preferences: JobSearchPreferences | None,
) -> None:
    sort_order = st.selectbox(
        "Sort matched listings",
        options=["Relevance", "Newest", "Location"],
        help="Choose how to order current resume-matched listings.",
        key="job_recommendation_sort_order",
    )
    ordered_recommendations = sort_job_recommendations(recommendations, sort_order)
    render_job_recommendations(
        ordered_recommendations, catalog_status, browse_jobs or [], preferences
    )


# ---------------------------------------------------------------------------
# Tab: Download Report
# ---------------------------------------------------------------------------


def _render_report_tab(report_bytes: bytes | None) -> None:
    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">Keep a copy</div>', unsafe_allow_html=True)
        st.subheader("Take your plan with you")
        st.caption(
            "Your downloadable PDF includes resume insights, matched roles,"
            " skill-development priorities, and quality-check results."
        )
        if report_bytes:
            st.download_button(
                "Download my report  ↓",
                data=report_bytes,
                file_name="resume-analysis.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        else:
            st.warning(
                "The PDF report could not be generated for this analysis."
                "  Your insights are still available in the tabs above."
            )
