"""End-to-end Streamlit workflow coverage with local fake services."""

from streamlit.testing.v1 import AppTest


def test_pasted_resume_builds_results_without_external_services():
    source = """
from datetime import UTC, datetime
from types import SimpleNamespace
import streamlit as st
from app.pages.analyze_resume import render_analyze_page
from app.pages.results import render_results_page
from models.analysis import ResumeAnalysis, Skill
from models.job import Job
from services.recommendation_service import RecommendationService

analysis = ResumeAnalysis(
    summary="Early-career data analyst with Python experience.",
    technical_skills=(Skill("Python", "Built a data project", False),),
    soft_skills=(),
    experience_assessment="Project experience demonstrates relevant exposure.",
    experience_highlights=("Built a data project",),
    learning_suggestions=("Practice SQL with a project.",),
    resume_improvements=(),
)
job = Job(
    "job-1",
    "Junior Data Analyst",
    "Analyze datasets",
    ("Python", "SQL"),
    "Bengaluru, India",
    "https://careers.example.org/job-1",
    "Synthetic fixture",
    datetime.now(UTC).date(),
)

class FakeResumeService:
    def parse_text(self, text):
        return SimpleNamespace(text=text)

class FakeAnalysisService:
    def analyze(self, text):
        return analysis

class FakeRepository:
    def list_active_jobs(self):
        return [job]

class FakeReportService:
    def generate(
        self, analysis, recommendations, skill_plan=None, quality_report=None, career_profile=None
    ):
        st.session_state["fake_report_generated"] = True
        return b"synthetic pdf"

render_analyze_page(
    FakeResumeService(),
    FakeAnalysisService(),
    RecommendationService(FakeRepository()),
    10 * 1024 * 1024,
    100_000,
)
render_results_page(FakeReportService(), RecommendationService(FakeRepository()))
"""
    app = AppTest.from_string(source).run(timeout=20)
    assert not app.exception

    next(button for button in app.button if button.label.startswith("Try a sample")).click().run(
        timeout=20
    )
    assert app.radio[0].value == "Paste resume text"
    assert app.text_area[0].value.startswith("=== DEMO RESUME — Synthetic data only")
    assert app.checkbox[0].value is False
    assert next(button for button in app.button if button.label.startswith("Analyze")).disabled

    app.text_area[0].set_value("Experience\\nPython data project\\n" + ("Analyzed datasets. " * 20))
    app.checkbox[0].check().run(timeout=20)
    next(button for button in app.button if button.label.startswith("Analyze")).click().run(
        timeout=20
    )

    assert not app.exception
    assert app.session_state["resume_analysis"].summary.startswith("Early-career")
    assert app.session_state["resume_source_text"].startswith("Experience")
    assert app.session_state["resume_quality_report"].compared_listing_count == 1
    assert [step.skill for step in app.session_state["skill_development_plan"]] == ["SQL"]
    assert app.session_state["fake_report_generated"] is True
    assert "demo_mode" not in app.session_state

    app.run(timeout=20)
    assert not app.exception
    assert app.checkbox[0].value is False
