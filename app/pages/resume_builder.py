"""Session-only resume creation and editing workspace."""

from __future__ import annotations

import hashlib
import re
from html import escape

import streamlit as st

from app.services.resume_service import ResumeService
from app.utils.errors import ApplicationError
from reports.resume_pdf_renderer import ResumePdfRenderer
from services.resume_builder_service import (
    ResumeDraft,
    build_contact_line,
    build_resume_sections,
    extract_contact_from_text,
    extract_name_from_text,
    review_resume_draft,
    split_existing_resume,
)

_EXISTING_TEXT_KEY = "resume_builder_existing_text"
_EXISTING_FINGERPRINT_KEY = "resume_builder_existing_fingerprint"
_TEMPLATES = ("Classic", "Modern", "Compact")


def render_resume_builder(resume_service: ResumeService) -> None:
    """Render guided resume-building and existing-resume editing flows."""
    st.markdown('<div class="section-eyebrow">Resume workspace</div>', unsafe_allow_html=True)
    st.title("Build or improve your resume")
    st.write("A guided workspace to shape your experience into a clear, professional resume.")
    with st.container(border=True):
        st.markdown("**Private by design**")
        st.caption(
            "Your content stays in this active browser session. This workspace does not send "
            "resume content to AI or save it to the database. Add only accurate information."
        )

    build_tab, edit_tab = st.tabs(["Create a resume", "Edit an existing resume"])
    with build_tab:
        _render_builder()
    with edit_tab:
        _render_editor(resume_service)


def _render_builder() -> None:
    st.markdown("### Your resume, step by step")
    st.caption(
        "Start with the sections you have. A strong student resume can lead with education "
        "and projects instead of employment history."
    )
    st.caption(
        "Complete each step in order. Open **Review & export** when you're ready to preview "
        "and download your resume."
    )

    profile_tab, education_tab, experience_tab, review_tab = st.tabs(
        ["Profile", "Education & skills", "Experience & projects", "Review & export"]
    )
    with profile_tab:
        name_col, role_col = st.columns(2)
        with name_col:
            full_name = st.text_input("Full name", key="resume_builder_name", max_chars=120)
        with role_col:
            target_role = st.text_input(
                "Target role (optional)",
                key="resume_builder_target_role",
                max_chars=120,
                placeholder="For example, Junior Data Analyst",
            )

        contact_col, phone_col = st.columns(2)
        with contact_col:
            email = st.text_input("Email", key="resume_builder_email", max_chars=254)
        with phone_col:
            phone = st.text_input("Phone (optional)", key="resume_builder_phone", max_chars=40)
        location_col, linkedin_col = st.columns(2)
        with location_col:
            location = st.text_input(
                "Location (optional)", key="resume_builder_location", max_chars=120
            )
        with linkedin_col:
            linkedin = st.text_input(
                "LinkedIn URL (optional)", key="resume_builder_linkedin", max_chars=250
            )
        portfolio = st.text_input(
            "Portfolio or GitHub URL (optional)",
            key="resume_builder_portfolio",
            max_chars=250,
        )
        summary = st.text_area(
            "Professional profile",
            key="resume_builder_summary",
            max_chars=1500,
            height=130,
            placeholder=(
                "In 2–4 lines, describe your direction, strongest relevant skills, and "
                "the evidence you can support."
            ),
            help="Keep it specific and truthful. Avoid generic claims such as “hard-working.”",
        )

    with education_tab:
        education = st.text_area(
            "Education",
            key="resume_builder_education",
            max_chars=4000,
            height=180,
            placeholder=(
                "Qualification | Institution | Graduation / expected date\n"
                "Relevant coursework, academic achievements, or honors."
            ),
            help="Put the most relevant or recent qualification first.",
        )
        skills = st.text_area(
            "Skills",
            key="resume_builder_skills",
            max_chars=2500,
            height=150,
            placeholder="Group relevant skills, for example: Languages: Python, SQL | Tools: Git",
            help="Only include skills you can explain or demonstrate with an example.",
        )

    with experience_tab:
        st.caption(
            "No formal job experience yet? Use projects, volunteering, student leadership, "
            "part-time work, or internships."
        )
        experience = st.text_area(
            "Experience, volunteering, or leadership",
            key="resume_builder_experience",
            max_chars=6000,
            height=190,
            placeholder=(
                "Role or activity | Organisation | Dates\n"
                "Describe what you did, the tools or skills used, and the outcome."
            ),
            help="Use one entry per role. Start bullets with an action and add a real outcome.",
        )
        projects = st.text_area(
            "Projects",
            key="resume_builder_projects",
            max_chars=6000,
            height=190,
            placeholder=(
                "Project name | Tools | Dates\n"
                "Problem solved, your contribution, and any measurable result."
            ),
            help="Coursework and personal projects are useful evidence for early-career roles.",
        )
        certifications = st.text_area(
            "Certifications, awards, or activities (optional)",
            key="resume_builder_certifications",
            max_chars=3000,
            height=130,
            placeholder="Relevant certification, award, club, or activity with dates.",
        )

    draft = ResumeDraft(
        full_name=full_name,
        email=email,
        phone=phone,
        location=location,
        target_role=target_role,
        linkedin=linkedin,
        portfolio=portfolio,
        summary=summary,
        education=education,
        skills=skills,
        experience=experience,
        projects=projects,
        certifications=certifications,
    )
    sections = build_resume_sections(draft)
    completeness, checks = review_resume_draft(draft)

    with review_tab:
        _render_review(draft, sections, completeness, checks)


def _render_review(
    draft: ResumeDraft,
    sections: list[tuple[str, str]],
    completeness: int,
    checks: list[tuple[str, str, str]],
) -> None:
    if not sections:
        st.info("Complete at least one section to see your resume preview and PDF download here.")
        return

    st.markdown("### Your resume is ready to review")
    st.caption(
        "The PDF follows this order: Profile, Education, Experience, Projects, Skills, "
        "then Certifications or activities."
    )
    _render_export(draft, sections)
    st.divider()
    st.markdown("### Resume completeness review")
    st.metric("Resume completeness", f"{completeness}%")
    st.progress(completeness / 100)
    st.caption("A section checklist only — not an ATS score or a measure of your suitability.")
    st.markdown("**Section review**")
    for label, status, suggestion in checks:
        with st.expander(f"{label} · {status}", expanded=status != "Complete"):
            st.write(suggestion)


def _render_export(draft: ResumeDraft, sections: list[tuple[str, str]]) -> None:
    template_col, download_col = st.columns([2, 1])
    with template_col:
        template = st.selectbox(
            "PDF layout",
            options=_TEMPLATES,
            key="resume_builder_template",
            help="Choose a clean, text-based layout. You can switch layouts before downloading.",
        )
        st.caption(
            {
                "Classic": "Centered name with a familiar, traditional section hierarchy.",
                "Modern": "Left-aligned header with a restrained teal accent.",
                "Compact": "Tighter spacing to make room for more content.",
            }[template]
        )
    pdf_bytes = ResumePdfRenderer().render(
        draft.full_name,
        build_contact_line(draft),
        sections,
        template=template,
        subtitle=draft.target_role,
    )
    with download_col:
        st.markdown("#### Download your resume")
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="resume.pdf",
            mime="application/pdf",
            type="primary",
            key="download_built_resume",
            use_container_width=True,
        )
        st.caption("Your resume is generated in this session. No AI or database storage.")

    _render_preview(
        draft.full_name,
        draft.target_role,
        build_contact_line(draft),
        sections,
    )


def _render_editor(resume_service: ResumeService) -> None:
    st.subheader("Edit your existing resume")
    st.caption(
        "Upload a PDF or DOCX to extract its text locally, or paste text directly. "
        "The original layout is not retained; review the extracted text before exporting."
    )
    uploaded_file = st.file_uploader(
        "Upload an existing resume",
        type=["pdf", "docx"],
        key="resume_builder_upload",
        help="This extracts text in the app session. It does not call AI.",
    )

    if uploaded_file is not None:
        content = uploaded_file.getvalue()
        fingerprint = hashlib.sha256(content).hexdigest()
        if st.session_state.get(_EXISTING_FINGERPRINT_KEY) != fingerprint:
            st.session_state[_EXISTING_FINGERPRINT_KEY] = fingerprint
            st.session_state[_EXISTING_TEXT_KEY] = ""
            st.session_state["resume_builder_editor_revision"] = (
                st.session_state.get("resume_builder_editor_revision", 0) + 1
            )
            try:
                parsed = resume_service.parse(uploaded_file.name, content)
            except ApplicationError as exc:
                st.error(exc.user_message)
            else:
                st.session_state[_EXISTING_TEXT_KEY] = parsed.text

    if _EXISTING_TEXT_KEY not in st.session_state:
        st.session_state[_EXISTING_TEXT_KEY] = ""
    revision = st.session_state.get("resume_builder_editor_revision", 0)
    edited_text = st.text_area(
        "Resume text",
        key=f"resume_builder_editor_{revision}",
        value=st.session_state[_EXISTING_TEXT_KEY],
        height=360,
        max_chars=resume_service.max_resume_chars,
        placeholder=(
            "Upload a PDF or DOCX above, or paste your existing resume text here to edit it."
        ),
    )
    st.session_state[_EXISTING_TEXT_KEY] = edited_text

    sections = split_existing_resume(edited_text)
    if not sections:
        st.caption("Add resume text to preview and download your edited version.")
        return

    template = st.selectbox(
        "Choose a PDF layout",
        options=_TEMPLATES,
        key="resume_builder_edit_template",
    )
    detected_name = extract_name_from_text(edited_text)
    detected_contact = extract_contact_from_text(edited_text)
    _render_preview(detected_name, "", detected_contact, sections)
    pdf_bytes = ResumePdfRenderer().render(
        detected_name, detected_contact, sections, template=template
    )
    st.download_button(
        "Download edited resume as PDF",
        data=pdf_bytes,
        file_name="edited_resume.pdf",
        mime="application/pdf",
        type="primary",
        key="download_edited_resume",
    )


_URL_HTML_RE = re.compile(
    r"(https?://[^\s<>\"'\)]+|(?:www\.|linkedin\.com/|github\.com/|codolio\.com/)[^\s<>\"'\)]+)",
    re.IGNORECASE,
)
_EMAIL_HTML_RE = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")


def _html_linkify(text: str) -> str:
    safe = escape(text)

    def _url_sub(m: re.Match) -> str:
        url = m.group(0).rstrip(".,;")
        href = url if url.startswith(("http://", "https://")) else f"https://{url}"
        return (
            f'<a href="{href}" target="_blank" rel="noopener noreferrer" '
            f'style="color:#2563eb;text-decoration:underline;">{url}</a>'
        )

    def _email_sub(m: re.Match) -> str:
        email = m.group(0)
        return (
            f'<a href="mailto:{email}" '
            f'style="color:#2563eb;text-decoration:underline;">{email}</a>'
        )

    safe = _URL_HTML_RE.sub(_url_sub, safe)
    safe = _EMAIL_HTML_RE.sub(_email_sub, safe)
    return safe


def _render_preview(
    name: str,
    target_role: str,
    contact_line: str,
    sections: list[tuple[str, str]],
) -> None:
    st.markdown("#### Resume page preview")
    with st.container(border=True):
        st.subheader(name.strip() or "Your name")
        if target_role.strip():
            st.markdown(f"**{escape(target_role.strip())}**")
        if contact_line.strip():
            st.markdown(
                f'<div style="color:#4b5563;font-size:0.88rem;margin-bottom:0.4rem;">{_html_linkify(contact_line.strip())}</div>',
                unsafe_allow_html=True,
            )

        for heading, content in sections:
            sec_parts = [
                '<div style="border-top:1px solid #374151;padding-top:0.4rem;margin-top:0.6rem;">',
                f'<div style="color:#111827;font-weight:700;letter-spacing:.04em;text-transform:uppercase;font-size:.85rem;margin-bottom:0.25rem;">{escape(heading)}</div>',
            ]
            for line in content.strip().split("\n"):
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith(("•", "-", "–", "▪", "■", "*", "·", "◦")):
                    bullet_text = stripped.lstrip("•-–▪■*·◦ ")
                    sec_parts.append(
                        f'<div style="padding-left:1.2rem;position:relative;line-height:1.55;font-size:0.88rem;color:#1f2937;">'
                        f'<span style="position:absolute;left:0.35rem;">•</span>{_html_linkify(bullet_text)}</div>'
                    )
                else:
                    sec_parts.append(
                        f'<div style="line-height:1.55;font-size:0.88rem;color:#1f2937;margin-bottom:0.2rem;">{_html_linkify(stripped)}</div>'
                    )
            sec_parts.append("</div>")
            st.markdown("".join(sec_parts), unsafe_allow_html=True)
