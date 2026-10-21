"""Streamlit tests for applying role and location preferences."""

from streamlit.testing.v1 import AppTest


def test_preferences_filter_jobs_without_rerunning_resume_analysis():
    source = """
from datetime import UTC, datetime
import streamlit as st
from app.pages.results import render_results_page
from app.session_state import (
    ANALYSIS_KEY,
    BROWSE_JOBS_KEY,
    JOB_CATALOG_STATUS_KEY,
    RECOMMENDATIONS_KEY,
    RESUME_TEXT_KEY,
)
from models.analysis import ResumeAnalysis, Skill
from models.job import Job
from services.recommendation_service import RecommendationService

posted = datetime.now(UTC).date()
jobs = [
    Job("software-bengaluru", "Graduate Software Engineer", "", ("Python", "SQL"), "Bengaluru, India", "https://careers.example.com/software", "Fixture", posted),
    Job("analyst-bengaluru", "Graduate Data Analyst", "", ("Python",), "Bengaluru, India", "https://careers.example.com/analyst", "Fixture", posted),
    Job("software-hyderabad", "Graduate Software Engineer", "", ("Python",), "Hyderabad, India", "https://careers.example.com/hyderabad", "Fixture", posted),
]
analysis = ResumeAnalysis(
    summary="Synthetic resume summary",
    technical_skills=(Skill("Python", "Built a Python project", False),),
    soft_skills=(),
    experience_assessment="Synthetic experience assessment",
    experience_highlights=(),
    learning_suggestions=(),
    resume_improvements=(),
)
st.session_state[ANALYSIS_KEY] = analysis
st.session_state[RECOMMENDATIONS_KEY] = []
st.session_state[BROWSE_JOBS_KEY] = jobs
st.session_state[RESUME_TEXT_KEY] = "Experience\\nPython projects"

class FakeReportService:
    def generate(
        self, analysis, recommendations, skill_plan=None, quality_report=None, career_profile=None
    ):
        return b"synthetic pdf"

render_results_page(
    FakeReportService(),
    RecommendationService(type("Repository", (), {"list_active_jobs": lambda self: jobs})()),
)
"""
    app = AppTest.from_string(source).run(timeout=20)

    assert not app.exception
    app.text_input[0].set_value("software engineer")
    app.text_input[1].set_value("Bengaluru")
    app.button[0].click().run(timeout=20)

    assert not app.exception
    assert app.session_state["job_search_preferences"].role_keywords == ("software engineer",)
    assert app.session_state["job_search_preferences"].location == "Bengaluru"
    assert [job.id for job in app.session_state["browse_current_jobs"]] == ["software-bengaluru"]
    assert [item.job.id for item in app.session_state["job_recommendations"]] == [
        "software-bengaluru"
    ]
    assert [step.skill for step in app.session_state["skill_development_plan"]] == ["SQL"]
    rendered_text = "\n".join(item.value for item in app.markdown)
    assert "Active filters" in "\n".join(item.value for item in app.caption)
    assert "Graduate Software Engineer" in rendered_text
    assert "Graduate Data Analyst" not in rendered_text

    app.text_input[0].set_value("")
    app.text_input[1].set_value("")
    app.button[0].click().run(timeout=20)

    assert not app.exception
    assert app.session_state["job_search_preferences"].has_filters is False
    assert len(app.session_state["browse_current_jobs"]) == 3
    assert len(app.session_state["job_recommendations"]) == 3
    assert [
        (step.skill, step.listing_count) for step in app.session_state["skill_development_plan"]
    ] == [("SQL", 1)]
