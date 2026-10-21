"""Resume submission and analysis page — redesigned home/landing experience."""

from __future__ import annotations

import logging

import streamlit as st

from app.components.career_profile import render_career_profile_form
from app.components.footer import render_footer
from app.components.home_sections import (
    maybe_load_sample_resume,
    render_how_it_works,
    render_value_cards,
)
from app.components.status_messages import show_application_error
from app.components.upload_form import render_upload_form
from app.services.resume_service import ResumeService
from app.session_state import (
    ANALYSIS_KEY,
    BROWSE_JOBS_KEY,
    CAREER_PROFILE_KEY,
    CORRELATION_ID_KEY,
    DEMO_MODE_KEY,
    JOB_CATALOG_STATUS_KEY,
    JOB_SEARCH_PREFERENCES_KEY,
    RECOMMENDATION_ERROR_KEY,
    RECOMMENDATIONS_KEY,
    RESUME_QUALITY_KEY,
    RESUME_TEXT_KEY,
    SKILL_DEVELOPMENT_PLAN_KEY,
    clear_analysis_state,
    get_current_user,
)
from app.utils.errors import ApplicationError
from app.utils.identifiers import new_correlation_id
from services.analysis_service import AnalysisService
from services.career_profile import CareerProfile
from services.recommendation_service import JobSearchPreferences, RecommendationService
from services.resume_quality_service import ResumeQualityService
from services.skill_development_service import SkillDevelopmentService

logger = logging.getLogger(__name__)


def render_analyze_page(
    resume_service: ResumeService,
    analysis_service: AnalysisService,
    recommendation_service: RecommendationService,
    max_upload_bytes: int,
    max_resume_chars: int,
) -> None:
    has_results = st.session_state.get(ANALYSIS_KEY) is not None

    # ── Hero ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="app-brand">
          <span class="app-brand-mark">R</span> Career clarity, one resume at a time
        </div>
        <div class="hero-kicker">Your next career move starts here</div>
        <h1>Understand your resume.<br><span class="hero-gradient-text">Discover fitting roles.</span><br>Plan your next skill.</h1>
        <p class="hero-copy">
          AI-powered resume insights, relevant job exploration, and a practical
          skill-development plan — grounded in what your resume actually says.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Step progress
    current_step = 3 if has_results else 1
    steps = [("1", "Add resume"), ("2", "AI review"), ("3", "Career plan")]
    progress_html = '<div class="step-track" aria-label="Analysis steps">'
    for index, (number, label) in enumerate(steps, start=1):
        state_class = "done" if index < current_step else "active" if index == current_step else ""
        symbol = "✓" if index < current_step else number
        progress_html += (
            f'<div class="step-item {state_class}">'
            f'<span class="step-number">{symbol}</span>'
            f"<span>{label}</span></div>"
        )
        if index < len(steps):
            progress_html += '<span class="step-divider" aria-hidden="true">›</span>'
    progress_html += "</div>"
    st.markdown(progress_html, unsafe_allow_html=True)

    current_user = get_current_user(st.session_state)
    if current_user is not None:
        user_display = current_user.full_name or current_user.username
        st.markdown(
            f'<div style="background: var(--color-periwinkle); border: 1px solid var(--color-mist); '
            f'border-radius: 14px; padding: 0.65rem 1.1rem; margin-bottom: 1rem; font-size: 0.92rem; color: var(--color-ink); '
            f'display: flex; align-items: center; gap: 0.65rem;">'
            f'<span style="display: inline-grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; '
            f'background: #6161ff; color: #ffffff; font-size: 0.75rem; font-weight: 700;">✓</span>'
            f'<span>Signed in as <strong>{user_display}</strong> (<code>@{current_user.username}</code>)</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # Loading the demo only inserts synthetic text into the paste field. The
    # normal consent gate still controls whether any analysis is sent to an AI.
    sample_text = maybe_load_sample_resume()
    if sample_text is not None:
        st.session_state[DEMO_MODE_KEY] = True
    if st.session_state.get(DEMO_MODE_KEY):
        st.info(
            "Demo resume loaded — synthetic data only. Review it below; analysis still "
            "requires your consent."
        )
        if st.button("Clear demo resume", key="clear_demo_resume"):
            st.session_state.pop(DEMO_MODE_KEY, None)
            st.session_state["resume_pasted_text"] = ""
            st.session_state["resume_input_method"] = "Upload a file"
            st.rerun()

    # ── Resume input ─────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(
            '<div class="section-eyebrow">Start with your resume</div>', unsafe_allow_html=True
        )
        uploaded_file, pasted_text, consent = render_upload_form(
            max_upload_bytes, max_resume_chars, initial_text=sample_text
        )
        st.caption(
            f"Accepted formats: PDF, DOCX, or TXT  ·  Maximum "
            f"{max_upload_bytes // (1024 * 1024)} MB per file"
        )
        st.caption("Resume text is sent to the AI provider only after you give consent below.")
        st.caption("This tool provides career guidance, not hiring decisions.")

    # ── Career profile (optional, collapsible) ───────────────────────────────
    with st.expander("Personalise your guidance (optional)", expanded=False):
        profile = render_career_profile_form()
        st.session_state[CAREER_PROFILE_KEY] = profile
    profile = st.session_state.get(CAREER_PROFILE_KEY, CareerProfile())

    # ── Job search preferences (pre-existing) ────────────────────────────────
    existing_prefs = st.session_state.get(JOB_SEARCH_PREFERENCES_KEY, JobSearchPreferences())
    preferred_location = profile.preferred_location or existing_prefs.location
    preferred_role = profile.preferred_role or (
        ", ".join(existing_prefs.role_keywords) if existing_prefs.role_keywords else ""
    )

    # ── Analyze button (always first button on page) ──────────────────────────
    has_resume = uploaded_file is not None or bool(pasted_text.strip())
    if st.button(
        "Analyze my resume  →",
        type="primary",
        disabled=not has_resume or not consent,
        use_container_width=True,
    ):
        st.session_state["resume_consent_cycle"] = (
            st.session_state.get("resume_consent_cycle", 0) + 1
        )
        correlation_id = new_correlation_id()
        st.session_state[CORRELATION_ID_KEY] = correlation_id
        clear_analysis_state(st.session_state)
        st.session_state[CORRELATION_ID_KEY] = correlation_id

        try:
            with st.spinner("Reviewing your resume and preparing career insights…"):
                if pasted_text.strip():
                    parsed_resume = resume_service.parse_text(pasted_text)
                elif uploaded_file is not None:
                    parsed_resume = resume_service.parse(
                        uploaded_file.name, uploaded_file.getvalue()
                    )
                else:
                    return

                analysis = analysis_service.analyze(parsed_resume.text)

            st.session_state[ANALYSIS_KEY] = analysis
            st.session_state[RESUME_TEXT_KEY] = parsed_resume.text

            # Build job search preferences from career profile + any existing prefs
            role_keywords_from_profile = (
                tuple(k.strip() for k in preferred_role.split(",") if k.strip())
                if preferred_role
                else existing_prefs.role_keywords
            )
            preferences = JobSearchPreferences(
                role_keywords=role_keywords_from_profile[:8],
                location=preferred_location.strip() or existing_prefs.location,
            )
            st.session_state[JOB_SEARCH_PREFERENCES_KEY] = preferences

            try:
                from app.config.settings import Settings
                from services.catalog_seeder import ensure_job_catalog

                ensure_job_catalog(
                    recommendation_service._repository,
                    Settings.from_environment(),
                )
                recommendations = recommendation_service.recommend(
                    analysis, preferences=preferences
                )
                st.session_state[RECOMMENDATIONS_KEY] = recommendations
                st.session_state[RECOMMENDATION_ERROR_KEY] = None
            except ApplicationError as exc:
                st.session_state[RECOMMENDATIONS_KEY] = []
                st.session_state[RECOMMENDATION_ERROR_KEY] = exc.user_message
                logger.warning(
                    "Recommendation lookup failed correlation_id=%s error_code=%s",
                    correlation_id,
                    type(exc).__name__,
                )

            try:
                st.session_state[JOB_CATALOG_STATUS_KEY] = recommendation_service.catalog_status(
                    preferences
                )
                st.session_state[BROWSE_JOBS_KEY] = recommendation_service.current_jobs(
                    limit=8, preferences=preferences
                )
                relevant_jobs = recommendation_service.current_jobs(
                    limit=100, preferences=preferences
                )
                st.session_state[RESUME_QUALITY_KEY] = ResumeQualityService().evaluate(
                    parsed_resume.text,
                    relevant_jobs,
                    career_stage=profile.stage,
                )
                st.session_state[SKILL_DEVELOPMENT_PLAN_KEY] = SkillDevelopmentService().build_plan(
                    analysis, relevant_jobs, resume_text=parsed_resume.text
                )
            except ApplicationError as exc:
                st.session_state[JOB_CATALOG_STATUS_KEY] = None
                st.session_state[BROWSE_JOBS_KEY] = []
                st.session_state[RESUME_QUALITY_KEY] = ResumeQualityService().evaluate(
                    parsed_resume.text,
                    career_stage=profile.stage,
                )
                st.session_state[SKILL_DEVELOPMENT_PLAN_KEY] = []
                logger.warning(
                    "Catalog status lookup failed correlation_id=%s error_code=%s",
                    correlation_id,
                    type(exc).__name__,
                )

            st.success("Your resume review is ready. Go to the Results page to see your insights.")

        except ApplicationError as exc:
            logger.warning(
                "Resume workflow failed correlation_id=%s error_code=%s",
                correlation_id,
                type(exc).__name__,
            )
            show_application_error(exc, correlation_id)
        except (OSError, ValueError):
            logger.exception(
                "Unexpected resume workflow failure correlation_id=%s",
                correlation_id,
            )
            st.error(
                f"Analysis could not be completed. Reference: {correlation_id}\n\n"
                "**Suggestions:** If you uploaded a file, try the 'Paste resume text' option."
                "  If you're using Gemini or OpenAI, check that the provider is reachable."
            )

    # Supporting context follows the primary resume action to keep submission
    # controls prominent, especially on narrower screens.
    if not has_results:
        render_value_cards()
    render_how_it_works()

    render_footer()
