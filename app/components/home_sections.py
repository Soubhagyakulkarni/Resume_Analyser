"""Hero section, value-preview cards, how-it-works panel, and sample-resume loader."""

from __future__ import annotations

import streamlit as st

from services.career_profile import SAMPLE_RESUME_TEXT

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------


def render_hero(has_results: bool) -> None:
    """Render the branded hero block with step progress indicator."""
    st.markdown(
        """
        <div class="app-brand">
          <span class="app-brand-mark">R</span> Career clarity, one resume at a time
        </div>
        <div class="hero-kicker">Your next career move starts here</div>
        <h1>Understand your resume.<br><span class="hero-gradient-text">Discover fitting roles.</span><br>Plan your next skill.</h1>
        <p class="hero-copy">
          Get AI-powered resume insights, discover relevant job roles, and build a practical
          skill-development plan — all grounded in what your resume actually says.
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
        "Resume Insights",
        "Understand what your resume demonstrates — and what it misses.",
    ),
    (
        "Relevant Job Roles",
        "Discover current listings that align with your skills.",
    ),
    (
        "Priority Skills",
        "Know which skills to learn next and why.",
    ),
    (
        "PDF Report",
        "Download a clear, shareable career-guidance report.",
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
1. **Upload or paste your resume.** PDF or DOCX files are extracted locally.
   Plain text pasting is also supported.
2. **Give consent.** Your resume text is sent to the configured AI provider
   *only* after you tick the consent checkbox.  No data is sent before that.
3. **Receive your analysis.** The app extracts skills, compares them against
   current job listings, and builds a skill-development plan.
4. **Explore and download.** Browse matched roles, review skill gaps, and
   download a PDF career-guidance report.

**Limitations to keep in mind:**
- AI analysis depends on resume text quality and provider availability.
- Job matches depend on catalog coverage and the 30-day freshness window.
- The app does not verify external profiles, repositories, or real abilities.
- No match does not mean the resume is poor or the user is unsuitable.
- This is career *guidance*, not an ATS score or hiring decision.
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
            help="Load a synthetic demo resume.  No real personal data.",
        )
    with col_note:
        st.caption(
            "**Demo only** — this is a synthetic resume for demonstration."
            "  No real person's data is used."
        )
    if clicked:
        return SAMPLE_RESUME_TEXT
    return None
