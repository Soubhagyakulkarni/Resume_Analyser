"""JD-vs-Resume tab: match score, missing keywords, before/after rewrites, skills chart."""

from __future__ import annotations

from html import escape

import streamlit as st

from models.analysis import ResumeAnalysis
from services.jd_matcher import JDMatchResult, match_jd


def render_jd_match_tab(analysis: ResumeAnalysis, resume_text: str) -> None:
    """Full JD analysis: paste JD → get score, gaps, rewrites."""
    st.markdown(
        '<div class="section-eyebrow">Job Description Analyser</div>',
        unsafe_allow_html=True,
    )
    st.subheader("How well does your resume match a role?")
    st.caption(
        "Paste the full job description below. The score is based on keyword overlap "
        "from the JD against your resume — no data is fabricated."
    )

    jd_text = st.text_area(
        "Paste the job description here",
        height=220,
        max_chars=15_000,
        placeholder=(
            "Paste the full job description, including required skills, "
            "responsibilities, and qualifications…"
        ),
        key="jd_input_text",
    )

    if not jd_text.strip():
        st.info("Paste a job description above to see your match score and tailored suggestions.")
        _render_skills_chart(analysis)
        return

    result: JDMatchResult = match_jd(resume_text, analysis, jd_text)

    if not result.all_jd_keywords:
        st.warning(
            "No recognisable keywords were found in the job description. "
            "Try pasting the full text including skills and requirements sections."
        )
        _render_skills_chart(analysis)
        return

    # ── Score gauge ─────────────────────────────────────────────────────────
    _render_score_gauge(result.score)

    st.divider()

    # ── Matched / missing columns ────────────────────────────────────────────
    col_matched, col_missing = st.columns(2, gap="large")

    with col_matched:
        with st.container(border=True):
            st.markdown(
                '<div class="section-eyebrow">In your resume ✓</div>',
                unsafe_allow_html=True,
            )
            st.subheader(f"Matched keywords ({len(result.matched_keywords)})")
            if result.matched_keywords:
                chips = " ".join(
                    f'<span class="skill-chip">{escape(kw)}</span>'
                    for kw in sorted(result.matched_keywords, key=str.casefold)
                )
                st.markdown(chips, unsafe_allow_html=True)
            else:
                st.caption("No JD keywords found in your resume.")

    with col_missing:
        with st.container(border=True):
            st.markdown(
                '<div class="section-eyebrow">Missing from resume ✗</div>',
                unsafe_allow_html=True,
            )
            st.subheader(f"Keywords to address ({len(result.missing_keywords)})")
            if result.missing_keywords:
                chips = " ".join(
                    f'<span style="display:inline-block;padding:4px 10px;margin:3px;'
                    f'border-radius:20px;background:#fee2e2;color:#991b1b;'
                    f'font-size:0.82rem;font-weight:500;">{escape(kw)}</span>'
                    for kw in sorted(result.missing_keywords, key=str.casefold)
                )
                st.markdown(chips, unsafe_allow_html=True)
                st.caption(
                    "These keywords appear in the JD but were not found in your resume. "
                    "Only add them if truthful — do not invent experience."
                )
            else:
                st.success("Your resume covers all detected JD keywords. 🎉")

    st.divider()

    # ── Before / after rewrite suggestions ──────────────────────────────────
    _render_rewrites(result)

    st.divider()

    # ── Skills bar chart ─────────────────────────────────────────────────────
    _render_skills_chart(analysis)


def _render_score_gauge(score: int) -> None:
    """Render a large animated score circle + colour-coded label."""
    if score >= 70:
        color, label = "#22c55e", "Strong match"
    elif score >= 40:
        color, label = "#f59e0b", "Moderate match"
    else:
        color, label = "#ef4444", "Low match — address missing keywords"

    # Pseudo-gauge via SVG progress ring
    radius = 54
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference * (1 - score / 100)

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:2rem;padding:1.2rem 0;">
          <div style="flex-shrink:0;position:relative;width:130px;height:130px;">
            <svg width="130" height="130" viewBox="0 0 130 130">
              <circle cx="65" cy="65" r="{radius}" fill="none"
                stroke="rgba(200,200,255,0.15)" stroke-width="12"/>
              <circle cx="65" cy="65" r="{radius}" fill="none"
                stroke="{color}" stroke-width="12" stroke-linecap="round"
                stroke-dasharray="{circumference:.1f}"
                stroke-dashoffset="{dash_offset:.1f}"
                transform="rotate(-90 65 65)"
                style="transition:stroke-dashoffset 0.8s ease"/>
            </svg>
            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
              text-align:center;line-height:1.2;">
              <div style="font-size:1.9rem;font-weight:800;color:{color};">{score}</div>
              <div style="font-size:0.7rem;color:#888;">/ 100</div>
            </div>
          </div>
          <div>
            <div style="font-size:1.35rem;font-weight:700;color:{color};">{label}</div>
            <div style="font-size:0.9rem;color:#888;margin-top:0.25rem;">
              Based on keyword overlap between the JD and your resume text.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_rewrites(result: JDMatchResult) -> None:
    """Before/after rewrite view with rule label."""
    with st.container(border=True):
        st.markdown(
            '<div class="section-eyebrow">Bullet rewrite suggestions</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Before & After")
        st.caption(
            "Structural suggestions only — no metrics are invented. "
            "Only include information that is truthful and accurate."
        )
        if not result.rewrite_suggestions:
            st.info(
                "No weak bullet patterns detected. Your bullets look structurally solid."
            )
            return
        for i, sug in enumerate(result.rewrite_suggestions, 1):
            with st.expander(f"Suggestion {i}: {sug.reason}", expanded=(i == 1)):
                before_col, after_col = st.columns(2, gap="medium")
                with before_col:
                    st.markdown("**Before** ❌")
                    st.markdown(
                        f'<div style="background:#fef2f2;border-left:4px solid #ef4444;'
                        f'padding:0.7rem 1rem;border-radius:6px;font-size:0.9rem;">'
                        f"{escape(sug.original_bullet)}</div>",
                        unsafe_allow_html=True,
                    )
                with after_col:
                    st.markdown("**After** ✅")
                    st.markdown(
                        f'<div style="background:#f0fdf4;border-left:4px solid #22c55e;'
                        f'padding:0.7rem 1rem;border-radius:6px;font-size:0.9rem;">'
                        f"{escape(sug.improved_bullet)}</div>",
                        unsafe_allow_html=True,
                    )
                st.caption(f"📏 Rule: *{sug.rule}*")


def _render_skills_chart(analysis: ResumeAnalysis) -> None:
    """Plotly bar chart of all skills detected in the resume."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.caption("Install plotly for the skills chart.")
        return

    tech = [(s.name, "Technical") for s in analysis.technical_skills]
    soft = [(s.name, "People") for s in analysis.soft_skills]
    skills = tech + soft

    if not skills:
        st.caption("No skills to chart.")
        return

    with st.container(border=True):
        st.markdown(
            '<div class="section-eyebrow">Skills overview</div>',
            unsafe_allow_html=True,
        )
        st.subheader("Your skills at a glance")
        st.caption("Derived from your resume analysis — only skills with evidence are shown.")

        names = [s[0] for s in skills]
        categories = [s[1] for s in skills]
        # confidence bar: inferred = 0.55, stated = 1.0
        inferred_set = {s.name for s in analysis.skills if s.inferred}
        values = [0.55 if n in inferred_set else 1.0 for n in names]
        colors = [
            "#6366f1" if cat == "Technical" else "#a78bfa"
            for cat in categories
        ]
        opacity = [0.6 if n in inferred_set else 1.0 for n in names]

        fig = go.Figure(
            go.Bar(
                x=values,
                y=names,
                orientation="h",
                marker_color=colors,
                marker_opacity=opacity,
                text=[
                    "Inferred" if n in inferred_set else "Evidenced" for n in names
                ],
                textposition="inside",
                insidetextanchor="start",
                hovertemplate="%{y}<br>Confidence: %{text}<extra></extra>",
            )
        )
        fig.update_layout(
            height=max(280, len(skills) * 28),
            margin=dict(l=0, r=20, t=10, b=20),
            xaxis=dict(
                range=[0, 1.1],
                tickvals=[0, 0.55, 1.0],
                ticktext=["0", "Inferred", "Evidenced"],
                showgrid=False,
            ),
            yaxis=dict(automargin=True),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", size=12, color="#e2e8f0"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Legend
        st.markdown(
            '<span style="display:inline-flex;align-items:center;gap:6px;margin-right:1rem;">'
            '<span style="width:12px;height:12px;border-radius:3px;background:#6366f1;display:inline-block;"></span>'
            " Technical</span>"
            '<span style="display:inline-flex;align-items:center;gap:6px;">'
            '<span style="width:12px;height:12px;border-radius:3px;background:#a78bfa;display:inline-block;"></span>'
            " People skills</span>",
            unsafe_allow_html=True,
        )
