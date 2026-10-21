"""Tiered skill-development plan view with optional weekly focus plan."""

from __future__ import annotations

import streamlit as st

from services.career_profile import WeeklyFocusWeek, build_weekly_focus, group_skill_tiers
from services.skill_development_service import SkillDevelopmentStep

_TIER_HELP = {
    "Start now": "Skills that appear in 3 or more selected listings — highest priority.",
    "Next": "Skills that appear in 2 selected listings.",
    "Optional": "Skills that appear in 1 selected listing — good stretch goals.",
}


def render_skill_plan(plan: list[SkillDevelopmentStep]) -> None:
    """Render the tiered skill-development plan."""
    if not plan:
        st.info(
            "No skill gaps were identified in the current selected listings."
            " Apply a target-role filter or refresh listings to build a role-specific plan."
        )
        return

    st.caption(
        "Skills listed here were found in current job listings but not evidenced in your resume."
        "  'Not found' does not mean you lack a skill — it means the resume didn't show it."
    )

    tiers = group_skill_tiers(plan)
    for tier in tiers:
        help_text = _TIER_HELP.get(tier.label, "")
        st.markdown(f"### {tier.label}")
        st.caption(help_text)
        for step in tier.steps:
            _render_skill_step(step)


def _render_skill_step(step: SkillDevelopmentStep) -> None:
    """Render a single skill-development step card."""
    with st.container(border=True):
        col_skill, col_count = st.columns([4, 1], vertical_alignment="center")
        with col_skill:
            st.markdown(f"#### {step.skill}")
        with col_count:
            st.metric(
                "Listings",
                step.listing_count,
                help=f"Appears in {step.listing_count} selected listing(s).",
            )

        # Why this skill
        role_label = ", ".join(step.roles) if step.roles else "current listings"
        st.caption(
            f"Appears in **{step.listing_count}** selected listing(s)"
            f" — roles include: {role_label}."
        )
        st.caption(
            "Resume evidence: this skill was not identified in the submitted resume. "
            "That does not mean you lack the skill."
        )

        # Resource or generic direction
        if step.resource:
            st.link_button(
                f"Learn from {step.resource.provider}: {step.resource.title} ↗",
                step.resource.url,
            )
        else:
            st.write(
                f"**General learning direction:** Build a small project that demonstrates"
                f" {step.skill}.  Search for official documentation or reputable tutorials."
            )
            st.caption("No vetted link is available yet for this skill.")

        # Optional weekly focus expander
        with st.expander(f"View 4-week plan for {step.skill}", expanded=False):
            _render_weekly_focus(build_weekly_focus(step.skill))


def _render_weekly_focus(weeks: list[WeeklyFocusWeek]) -> None:
    """Render a compact four-week focus plan."""
    for week in weeks:
        st.markdown(f"**Week {week.week} — {week.theme}**")
        for action in week.actions:
            st.markdown(f"- {action}")
        st.write("")
