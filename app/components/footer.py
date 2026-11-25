"""App footer with privacy and career-guidance disclosures."""

from __future__ import annotations

import streamlit as st


def render_footer() -> None:
    """Render the app-wide footer."""
    st.markdown(
        """
        <div class="app-footer">
          <div class="app-footer-meta">
            <span>Career guidance only — not an ATS score or hiring decision.</span>
            <span>Resume text is shared with the configured AI provider only after consent; it stays in your session, not the database.</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
