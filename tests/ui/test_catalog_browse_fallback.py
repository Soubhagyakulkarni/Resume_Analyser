"""Tests for showing current listings when skill matching finds no roles."""

from streamlit.testing.v1 import AppTest


def test_current_jobs_are_labeled_as_browse_only_when_no_skill_match():
    source = """
from datetime import UTC, datetime
from app.components.analysis_view import render_analysis
from models.analysis import ResumeAnalysis
from models.job import Job
from services.recommendation_service import JobCatalogStatus

analysis = ResumeAnalysis(
    summary="Synthetic resume summary",
    technical_skills=(),
    soft_skills=(),
    experience_assessment="Synthetic experience assessment",
    experience_highlights=(),
    learning_suggestions=(),
    resume_improvements=(),
)
job = Job(
    id="synthetic-job",
    title="Graduate Software Engineer",
    description="Synthetic fixture listing",
    required_skills=(),
    location="Hyderabad",
    application_url="https://jobs.example.org/role",
    source="Synthetic fixture",
    updated_at=datetime.now(UTC).date(),
)
render_analysis(
    analysis,
    [],
    JobCatalogStatus(25, 25, 25, 0, 0, 30, datetime.now(UTC).date()),
    [job],
)
"""
    app = AppTest.from_string(source).run(timeout=20)

    assert not app.exception
    markdown = "\n".join(item.value for item in app.markdown)
    captions = "\n".join(item.value for item in app.caption)
    assert "No skill-based matches found" in markdown
    assert "not a judgment about your ability" in markdown
    assert "Graduate Software Engineer" in markdown
    assert "not ranked or matched to your resume" in captions
    assert "Showing 1 of 25 current listings" in captions
