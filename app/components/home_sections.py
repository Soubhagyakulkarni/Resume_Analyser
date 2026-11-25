"""Hero section, value-preview cards, how-it-works panel, and sample-resume loader."""

from __future__ import annotations

import streamlit as st

from services.career_profile import SAMPLE_RESUME_TEXT

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------


def render_hero(has_results: bool) -> None:
    """Render the concise hero block and step progress indicator."""
    st.markdown(
        """
        <div class="hero-kicker">Resume analysis</div>
        <h1>Plan your next career move.</h1>
        <p class="hero-copy">
          Review your resume, explore relevant roles, and identify skills to build.
        </p>
        """,
        unsafe_allow_html=True,
    )
    _render_step_progress(has_results)


def _render_step_progress(has_results: bool) -> None:
    current_step = 3 if has_results else 1
    steps = [("1", "Add resume"), ("2", "AI review"), ("3", "Career plan")]
    html = '<div class="step-track" aria-label="Analysis steps">'
    for index, (number, label) in enumerate(steps, start=1):
        state_class = "done" if index < current_step else "active" if index == current_step else ""
        symbol = "✓" if index < current_step else number
        html += (
            f'<div class="step-item {state_class}">'
            f'<span class="step-number">{symbol}</span>'
            f"<span>{label}</span></div>"
        )
        if index < len(steps):
            html += '<span class="step-divider" aria-hidden="true">›</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Value preview cards
# ---------------------------------------------------------------------------

_VALUE_CARDS = [
    (
        "Resume review",
        "Strengths, gaps, and actionable feedback.",
    ),
    (
        "Job matches",
        "Current roles based on your experience.",
    ),
    (
        "Skills plan",
        "Prioritized skills to strengthen your profile.",
    ),
    (
        "PDF Report",
        "Download a summary of your results.",
    ),
]


def render_value_cards() -> None:
    """Show 4 compact pastel value-proposition cards."""
    st.markdown('<div class="section-eyebrow">What you\'ll get</div>', unsafe_allow_html=True)
    cols = st.columns(len(_VALUE_CARDS))
    for col, (title, desc) in zip(cols, _VALUE_CARDS):
        with col:
            st.markdown(
                f"""
                <div class="value-card">
                  <div class="value-card-title">{title}</div>
                  <div class="value-card-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# How-it-works panel
# ---------------------------------------------------------------------------


def render_how_it_works() -> None:
    """Render a compact three-step process explanation."""
    with st.expander("How this works", expanded=False):
        st.markdown(
            """
1. Upload or paste your resume.
2. Review and consent before sending it for AI analysis.
3. Explore resume feedback, job matches, and a skills plan.

**Keep in mind:** Matches depend on available listings and resume evidence.
Review AI suggestions for accuracy. Results are career guidance, not hiring decisions.
            """
        )


# ---------------------------------------------------------------------------
# Sample resume loader
# ---------------------------------------------------------------------------


def maybe_load_sample_resume() -> str | None:
    """Show a "Try a sample resume" button.  Returns sample text when clicked, else None."""
    col_btn, col_note = st.columns([2, 5])
    with col_btn:
        clicked = st.button(
            "Try a sample resume",
            key="load_sample_resume",
            help="Load a sample with synthetic data.",
        )
    with col_note:
        st.caption("Sample data only; no real personal information.")
    if clicked:
        return SAMPLE_RESUME_TEXT
    return None
