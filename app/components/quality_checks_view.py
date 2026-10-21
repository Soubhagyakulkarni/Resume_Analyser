"""Renamed Resume Quality Checks view (previously "ATS-friendly resume checks")."""

from __future__ import annotations

import streamlit as st

from services.resume_quality_service import ResumeQualityFinding, ResumeQualityReport


def render_quality_checks(quality_report: ResumeQualityReport | None) -> None:
    """Render Resume Quality Checks with pass / needs-attention / not-detected status."""
    st.markdown(
        """
        <div class="quality-disclaimer">
          <strong>Resume Quality Checks</strong> — these checks improve resume clarity,
          structure, and keyword alignment.  They do not simulate a specific employer's
          ATS or predict screening results.  Passing all checks does not guarantee
          any outcome.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if quality_report is None:
        st.info("Resume checks are unavailable for this analysis.")
        return

    if quality_report.compared_listing_count:
        st.caption(
            f"Keyword comparison uses skill terms from"
            f" {quality_report.compared_listing_count} selected current listing(s)."
        )

    # Summary progress bar (pass rate)
    total = len(quality_report.findings)
    passing = sum(
        1
        for f in quality_report.findings
        if f.status.casefold() in {"looks readable", "looks clear", "found"}
    )
    if total:
        pass_rate = passing / total
        st.progress(
            pass_rate,
            text=f"**{passing} of {total}** checks passed — quality indicator only, not an ATS score",
        )

    st.write("")
    for finding in quality_report.findings:
        _render_finding(finding)


def _render_finding(finding: ResumeQualityFinding) -> None:
    label = _friendly_status_label(finding.status)

    with st.expander(f"{label} — {finding.title}", expanded=False):
        st.write(finding.detail)
        if finding.suggestion:
            st.markdown(
                f'<div class="check-suggestion"><strong>Suggestion:</strong>'
                f" {finding.suggestion}</div>",
                unsafe_allow_html=True,
            )


def _friendly_status_label(status: str) -> str:
    mapping = {
        "looks readable": "Pass",
        "looks clear": "Pass",
        "found": "Pass",
        "review": "Needs attention",
        "optional improvement": "Optional improvement",
        "not assessed": "Not assessed",
        "not detected": "Not detected",
    }
    return mapping.get(status.casefold(), status)
