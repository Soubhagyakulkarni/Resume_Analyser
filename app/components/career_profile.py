"""Career profile personalization form (optional, non-blocking)."""

from __future__ import annotations

import streamlit as st

from services.career_profile import CareerProfile


def render_career_profile_form() -> CareerProfile:
    """Render the optional career profile section and return the current profile.

    The form is non-blocking: all fields have empty defaults, and the user
    can skip it entirely.  Profile data is stored in session state only.
    """
    st.markdown(
        '<div class="section-eyebrow">Optional — personalise your guidance</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Career profile")
    st.caption(
        "Sharing a bit about where you are and what you want helps tailor the"
        " recommendations and skill priorities.  All fields are optional and"
        " are kept only for this session."
    )

    col_stage, col_goal = st.columns(2)
    with col_stage:
        stage = st.selectbox(
            "Career stage",
            options=["", "Student", "Fresher", "Early-career", "Experienced"],
            index=0,
            format_func=lambda x: "Not specified" if x == "" else x,
            key="cp_stage",
            help="Pick the stage that best describes you right now.",
        )
    with col_goal:
        goal = st.selectbox(
            "Primary goal",
            options=["", "Internship", "First job", "Career switch", "Upskilling"],
            index=0,
            format_func=lambda x: "Not specified" if x == "" else x,
            key="cp_goal",
            help="What are you mainly trying to achieve right now?",
        )

    col_role, col_loc = st.columns(2)
    with col_role:
        preferred_role = st.text_input(
            "Preferred role or field",
            value="",
            placeholder="e.g. Data Analyst, Frontend Developer",
            max_chars=100,
            key="cp_role",
            help="Optional.  Helps surface relevant listings.",
        )
    with col_loc:
        preferred_location = st.text_input(
            "Preferred location",
            value="",
            placeholder="e.g. Bengaluru, Remote",
            max_chars=100,
            key="cp_location",
            help="Optional.  Narrows job results by geography.",
        )

    return CareerProfile(
        stage=stage,  # type: ignore[arg-type]
        goal=goal,  # type: ignore[arg-type]
        preferred_role=preferred_role.strip(),
        preferred_location=preferred_location.strip(),
    )
