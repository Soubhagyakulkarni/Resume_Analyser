"""App footer with product name, disclaimer, privacy note, and version."""

from __future__ import annotations

import streamlit as st

_APP_VERSION = "0.1.0"


def render_footer() -> None:
    """Render the app-wide footer."""
    st.markdown(
        f"""
        <div class="app-footer">
          <div class="app-footer-brand">
            <span class="app-footer-mark">R</span>
            <span class="app-footer-name">AI Resume Analyzer</span>
          </div>
          <div class="app-footer-tagline">
            AI-powered resume insights and career guidance.
          </div>
          <div class="app-footer-meta">
            <span>
              <strong>Disclaimer:</strong> This tool provides career guidance only.
              It is not an ATS score, a hiring decision, or a job guarantee.
            </span>
            <span>
              <strong>Privacy:</strong> Resume text is sent to the configured AI provider
              only after explicit consent. It is held transiently in your session and is
              not stored in the database.
            </span>
            <span>Version {_APP_VERSION}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
