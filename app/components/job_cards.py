"""Redesigned job-match cards and browse-only listing cards."""

from __future__ import annotations

from html import escape
from urllib.parse import urlparse

import streamlit as st

from models.job import Job, JobRecommendation
from services.career_profile import classify_match_strength
from services.recommendation_service import JobCatalogStatus, JobSearchPreferences

_STRENGTH_STYLES: dict[str, str] = {
    "Strong": "match-chip-strong",
    "Moderate": "match-chip-moderate",
    "Exploratory": "match-chip-exploratory",
}


def render_job_recommendations(
    recommendations: list[JobRecommendation],
    catalog_status: JobCatalogStatus | None,
    browse_jobs: list[Job] | None,
    preferences: JobSearchPreferences | None,
) -> None:
    """Render matched recommendations, empty states, and browse-only listings."""
    if preferences and preferences.has_filters:
        applied = []
        if preferences.role_keywords:
            applied.append(f"Roles: {', '.join(preferences.role_keywords)}")
        if preferences.location.strip():
            applied.append(f"Location: {preferences.location.strip()}")
        st.caption("Active filters — " + " · ".join(applied))

    if catalog_status:
        if catalog_status.stale_count:
            st.caption(
                f"{catalog_status.stale_count} stale listing(s) older than"
                f" {catalog_status.max_age_days} days are excluded."
            )
        if catalog_status.future_dated_count:
            st.caption(f"{catalog_status.future_dated_count} future-dated listing(s) are excluded.")

    if recommendations:
        st.markdown(
            f"**{len(recommendations)} role{'s' if len(recommendations) != 1 else ''}"
            " matched your resume skills.**"
        )
        st.caption(
            "Match strength is based on the overlap between skills listed in the job"
            " description and skills found in your resume.  It is not a hiring probability."
        )
        for item in recommendations:
            _render_match_card(item)
    else:
        _render_empty_state(catalog_status)

    # Browse-only section (shown when no matches found and listings exist)
    if (
        not recommendations
        and catalog_status
        and catalog_status.preference_match_count
        and browse_jobs
    ):
        st.markdown("---")
        st.markdown("#### Browse current listings")
        st.caption(
            f"Showing {len(browse_jobs)} of {catalog_status.preference_match_count}"
            " current listings. "
            "These listings are not ranked or matched to your resume. "
            "Review each role's requirements to decide whether it suits you."
        )
        for job in browse_jobs:
            _render_browse_card(job)


def _render_match_card(item: JobRecommendation) -> None:
    """Render a single job-match card with skill chips and match context."""
    strength = classify_match_strength(item.match_ratio)
    strength_class = _STRENGTH_STYLES.get(strength, "match-chip-exploratory")

    with st.container(border=True):
        # Header row
        title_col, strength_col = st.columns([3, 1], vertical_alignment="center")
        with title_col:
            st.markdown(f"### {item.job.title}")
        with strength_col:
            st.markdown(
                f'<span class="match-strength-chip {strength_class}">{strength} match</span>',
                unsafe_allow_html=True,
            )

        # Meta
        posted = item.job.updated_at.isoformat()
        location_str = item.job.location or "Location not listed"
        st.caption(f"{location_str}  ·  Updated {posted}  ·  {item.job.source}")
        st.caption("Company information is not available in this listing.")
        if item.job.description:
            summary = " ".join(item.job.description.split())
            st.write(summary[:320] + ("…" if len(summary) > 320 else ""))

        # Rationale / context
        matched_count = len(item.matched_skills)
        total_count = matched_count + len(item.missing_from_resume)
        st.write(
            f"**{matched_count} of {total_count}** core skills from this listing"
            " were found in your resume."
        )

        # Skill chips
        if item.matched_skills:
            chips_html = "".join(
                f'<span class="skill-chip skill-chip-match">{escape(s)}</span>'
                for s in item.matched_skills
            )
            st.markdown(f"**Found in resume:** {chips_html}", unsafe_allow_html=True)

        if item.missing_from_resume:
            missing_html = "".join(
                f'<span class="skill-chip skill-chip-gap">{escape(s)}</span>'
                for s in item.missing_from_resume
            )
            st.markdown(f"**Not found in resume:** {missing_html}", unsafe_allow_html=True)
            first_gap = item.missing_from_resume[0]
            st.caption(
                f"To improve this match, add truthful evidence of {first_gap}"
                " (and other missing skills) to your resume."
            )

        # Apply link
        if item.job.application_url:
            host = urlparse(item.job.application_url).hostname or "external site"
            st.link_button(
                f"View listing at {host} ↗",
                item.job.application_url,
                type="secondary",
            )


def _render_browse_card(job: Job) -> None:
    """Render a browse-only listing card (no skill matching shown)."""
    with st.container(border=True):
        st.markdown(f"### {job.title}")
        location_str = job.location or "Location not listed"
        st.caption(f"{location_str}  ·  Posted {job.updated_at.isoformat()}  ·  {job.source}")
        if job.application_url:
            host = urlparse(job.application_url).hostname or "external site"
            st.link_button(f"Review listing at {host} ↗", job.application_url)


def _render_empty_state(catalog_status: JobCatalogStatus | None) -> None:
    """Render a friendly, informative empty state when no matches are found."""
    with st.container(border=True):
        st.markdown('<div class="section-eyebrow">Job catalog</div>', unsafe_allow_html=True)
        if catalog_status is None:
            st.markdown("#### Job listing status unavailable")
            st.write(
                "Your resume insights are ready, but the current job catalog status"
                " could not be checked. Please try again later."
            )
        elif catalog_status.total_count == 0:
            st.markdown("#### No current listings available")
            st.write(
                "Your resume insights are ready, but the job catalog is empty."
                " Recommendations will appear here when current listings are imported."
            )
        elif catalog_status.current_count == 0:
            st.markdown("#### No listings within the freshness window")
            st.write(
                f"{catalog_status.stale_count} listing(s) are older than"
                f" {catalog_status.max_age_days} days and"
                f" {catalog_status.future_dated_count} are future-dated."
                " Refresh the job feed to see current opportunities."
            )
        elif catalog_status.preference_match_count == 0:
            st.markdown("#### No current listings match these search filters")
            st.write(
                "Try a broader role keyword or location, or clear the filters."
                " This does not mean there are no suitable jobs for you."
            )
        else:
            st.markdown("#### No skill-based matches found")
            st.write(
                f"{catalog_status.preference_match_count} current listing(s) match your"
                " search filters, but none matched the skills identified in this resume."
                " This is not a judgment about your ability or overall job suitability."
            )
