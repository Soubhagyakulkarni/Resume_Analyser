"""Accessible resume upload controls."""

from typing import Any

import streamlit as st

_CONSENT_CYCLE_KEY = "resume_consent_cycle"


def render_upload_form(
    max_upload_bytes: int, max_resume_chars: int, initial_text: str | None = None
) -> tuple[Any | None, str, bool]:
    st.session_state.setdefault(_CONSENT_CYCLE_KEY, 0)
    if initial_text is not None:
        st.session_state["resume_input_method"] = "Paste resume text"
        st.session_state["resume_pasted_text"] = initial_text
        st.session_state[_consent_widget_key()] = False
    st.session_state.setdefault("resume_input_method", "Upload a file")
    st.session_state.setdefault("resume_pasted_text", "")

    st.subheader("Share your experience")
    st.write(
        "Choose the option that works best. We’ll turn your resume into clear, actionable feedback."
    )
    input_method = st.radio(
        "How would you like to add your resume?",
        ["Upload a file", "Paste resume text"],
        horizontal=True,
        label_visibility="visible",
        key="resume_input_method",
    )
    uploaded_file = None
    pasted_text = ""
    if input_method == "Upload a file":
        uploaded_file = st.file_uploader(
            "Drop your resume here or browse files",
            type=["pdf", "docx", "txt"],
            help=(
                f"PDF, DOCX, or TXT, up to {max_upload_bytes // (1024 * 1024)} MB. "
                "Only upload a resume you are authorized to share."
            ),
            label_visibility="visible",
        )
    else:
        pasted_text = st.text_area(
            "Resume text",
            height=240,
            max_chars=max_resume_chars,
            placeholder=(
                "Paste your resume text here, including experience, education, "
                "projects, and skills..."
            ),
            help=(
                f"Maximum {max_resume_chars:,} characters. "
                "Paste only content you are authorized to share."
            ),
            key="resume_pasted_text",
        )
    consent = st.checkbox(
        "I agree to send my resume to the configured AI provider for this analysis.",
        value=False,
        key=_consent_widget_key(),
    )
    return uploaded_file, pasted_text, consent


def _consent_widget_key() -> str:
    cycle = st.session_state.get(_CONSENT_CYCLE_KEY, 0)
    return f"resume_processing_consent_{cycle}"
