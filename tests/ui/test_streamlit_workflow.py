"""Presentation-state tests that run without a browser or OpenAI account."""

from app.session_state import (
    ANALYSIS_KEY,
    CORRELATION_ID_KEY,
    RECOMMENDATIONS_KEY,
    clear_analysis_state,
)


def test_reset_clears_transient_analysis_and_correlation_state():
    state = {
        ANALYSIS_KEY: object(),
        RECOMMENDATIONS_KEY: [],
        CORRELATION_ID_KEY: "opaque-id",
        "user_preference": "remote",
    }
    clear_analysis_state(state)

    assert ANALYSIS_KEY not in state
    assert RECOMMENDATIONS_KEY not in state
    assert CORRELATION_ID_KEY not in state
    assert state["user_preference"] == "remote"


def test_streamlit_entrypoint_explains_missing_api_key(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    app = AppTest.from_string(
        """
from types import SimpleNamespace
import app.main as application

application._build_services = lambda: SimpleNamespace(
    analysis=None, recommendations=None, report=None, auth=None, resume=None
)
application.main()
"""
    ).run(timeout=10)

    assert any("Set OPENAI_API_KEY" in item.value for item in app.error)


def test_streamlit_entrypoint_explains_missing_gemini_key(monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    app = AppTest.from_string(
        """
from types import SimpleNamespace
import app.main as application

application._build_services = lambda: SimpleNamespace(
    analysis=None, recommendations=None, report=None, auth=None, resume=None
)
application.main()
"""
    ).run(timeout=10)

    assert any("Set GEMINI_API_KEY" in item.value for item in app.error)


def test_streamlit_entrypoint_explains_missing_supabase_setup():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_string(
        """
import app.main as application

def missing_supabase():
    raise ValueError(
        "Create a Supabase project, run the documented SQL migration, and set "
        "SUPABASE_URL and SUPABASE_ANON_KEY."
    )

application._build_services = missing_supabase
application.main()
"""
    ).run(timeout=10)

    assert not app.exception
    assert any("Create a Supabase project" in item.value for item in app.error)


def test_results_page_explains_that_resume_analysis_is_required():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_string(
        """
from app.pages.results import render_results_page
render_results_page(None, None)
"""
    ).run(timeout=10)

    assert not app.exception
    assert any("Your resume insights will appear here" in item.value for item in app.header)
    assert any("Analyze resume page" in item.value for item in app.markdown)
