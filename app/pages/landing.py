"""Home and about pages."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.components.footer import render_footer

_IMAGE_DIR = Path(__file__).resolve().parents[1] / "assets" / "images"


def render_home_page(analyze_page: st.Page, resume_builder_page: st.Page) -> None:
    """Render the public landing page."""
    with st.container(key="home_hero"):
        copy, visual = st.columns([1.05, 0.95], gap="large", vertical_alignment="center")
        with copy:
            st.markdown('<div class="hero-kicker">CAREER TOOLS</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="home-hero-title">Make your experience easy to understand.</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p class="home-hero-copy">Review your resume, explore relevant roles, '
                "and build a clean, single-column PDF.</p>",
                unsafe_allow_html=True,
            )
            analyze, build = st.columns(2)
            with analyze, st.container(key="home_analyze_cta"):
                st.page_link(analyze_page, label="Analyse resume", width="stretch")
            with build, st.container(key="home_build_cta"):
                st.page_link(
                    resume_builder_page, label="Build your resume", width="stretch"
                )
        with visual:
            st.markdown(
                """
                <div class="home-product-preview">
                  <div class="home-preview-toolbar">
                    <span>RESUME PREVIEW</span><span>Sample layout</span>
                  </div>
                  <div class="home-resume-sheet">
                    <div class="home-resume-name">Jordan Lee</div>
                    <div class="home-resume-role">Product Designer</div>
                    <div class="home-resume-rule"></div>
                    <div class="home-resume-section">EXPERIENCE</div>
                    <div class="home-resume-line home-resume-line--strong"></div>
                    <div class="home-resume-line"></div>
                    <div class="home-resume-line home-resume-line--short"></div>
                    <div class="home-resume-section">EDUCATION</div>
                    <div class="home-resume-line home-resume-line--strong"></div>
                    <div class="home-resume-line home-resume-line--short"></div>
                  </div>
                  <div class="home-preview-tag">Single-column PDF</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.container(key="home_features"):
        st.markdown('<div class="section-eyebrow">WHAT YOU CAN DO</div>', unsafe_allow_html=True)
        st.subheader("Resume and job tools")
        features = (
            (
                "analysis",
                "career-portrait.jpg",
                "Resume analysis",
                "Understand strengths and areas to improve.",
            ),
            (
                "jobs",
                "career-team.jpg",
                "Job recommendations",
                "Explore current roles related to your skills.",
            ),
            (
                "builder",
                "career-work.jpg",
                "Resume builder",
                "Create a clear PDF using your own details.",
            ),
        )
        columns = st.columns(len(features), gap="medium")
        for column, (key, image, title, description) in zip(columns, features):
            with column, st.container(key=f"home_feature_{key}", border=True):
                st.image(str(_IMAGE_DIR / image), width="stretch")
                st.markdown(f"### {title}")
                st.write(description)
        st.caption("Photography: Unsplash")

    render_footer()


def render_about_page() -> None:
    """Explain the product without making unverifiable company claims."""
    st.markdown('<div class="section-eyebrow">About ResumeAI</div>', unsafe_allow_html=True)
    st.title("Career tools grounded in your experience")
    st.write(
        "ResumeAI helps you review the information in your resume, explore current job listings, "
        "and prepare a clear, text-based resume."
    )

    columns = st.columns(3)
    cards = (
        ("Resume analysis", "Review skills, experience, and areas to strengthen."),
        ("Job discovery", "Compare your listed skills with current opportunities."),
        ("Resume builder", "Create a single-column resume with selectable text."),
    )
    for column, (title, description) in zip(columns, cards):
        with column, st.container(border=True):
            st.markdown(f"### {title}")
            st.write(description)

    st.markdown("### Privacy and limitations")
    st.write(
        "Resume text is shared with the configured AI provider only after consent. "
        "Results are career guidance, not an ATS score or hiring decision; verify suggestions "
        "and include only accurate information."
    )
    render_footer()
