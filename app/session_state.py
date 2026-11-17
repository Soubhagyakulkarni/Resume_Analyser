"""Transient Streamlit workflow state."""

from collections.abc import MutableMapping
from typing import Any

ANALYSIS_KEY = "resume_analysis"
RECOMMENDATIONS_KEY = "job_recommendations"
RECOMMENDATION_ERROR_KEY = "recommendation_error"
JOB_CATALOG_STATUS_KEY = "job_catalog_status"
BROWSE_JOBS_KEY = "browse_current_jobs"
JOB_SEARCH_PREFERENCES_KEY = "job_search_preferences"
RESUME_TEXT_KEY = "resume_source_text"
RESUME_QUALITY_KEY = "resume_quality_report"
SKILL_DEVELOPMENT_PLAN_KEY = "skill_development_plan"
REPORT_KEY = "analysis_report"
CORRELATION_ID_KEY = "correlation_id"

# Optional session-only personalization; not cleared between analyses.
CAREER_PROFILE_KEY = "career_profile"

# Set to True when the sample/demo resume is loaded (cleared on real analysis).
DEMO_MODE_KEY = "demo_mode"

# Logged-in authenticated user identity; preserved across analyses.
AUTH_USER_KEY = "authenticated_user"


def get_current_user(state: MutableMapping[str, Any]) -> Any | None:
    """Return the currently authenticated user from session state if present."""
    return state.get(AUTH_USER_KEY)


def set_current_user(state: MutableMapping[str, Any], user: Any | None) -> None:
    """Set the authenticated user in session state."""
    if user is None:
        state.pop(AUTH_USER_KEY, None)
    else:
        state[AUTH_USER_KEY] = user


def logout_user(state: MutableMapping[str, Any]) -> None:
    """Log out the current user by removing the authenticated user from session state."""
    state.pop(AUTH_USER_KEY, None)


def clear_analysis_state(state: MutableMapping[str, Any]) -> None:
    """Clear per-analysis keys. Career profile and auth user are preserved across analyses."""
    for key in (
        ANALYSIS_KEY,
        RECOMMENDATIONS_KEY,
        RECOMMENDATION_ERROR_KEY,
        JOB_CATALOG_STATUS_KEY,
        BROWSE_JOBS_KEY,
        RESUME_TEXT_KEY,
        RESUME_QUALITY_KEY,
        SKILL_DEVELOPMENT_PLAN_KEY,
        REPORT_KEY,
        CORRELATION_ID_KEY,
        DEMO_MODE_KEY,
    ):
        state.pop(key, None)
