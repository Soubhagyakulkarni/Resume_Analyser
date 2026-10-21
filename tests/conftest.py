"""Shared synthetic data and isolated dependencies for pytest."""

from datetime import UTC, datetime

import pytest

from models.analysis import ResumeAnalysis, Skill
from models.job import Job


@pytest.fixture
def sample_analysis() -> ResumeAnalysis:
    return ResumeAnalysis(
        summary="Early-career candidate with Python project experience.",
        technical_skills=(Skill("Python", "Built a Python data project", False),),
        soft_skills=(),
        experience_assessment="Project experience demonstrates early-career technical exposure.",
        experience_highlights=("Built a Python data project",),
        learning_suggestions=("Practice SQL with a small portfolio project.",),
        resume_improvements=(),
    )


@pytest.fixture
def sample_job() -> Job:
    return Job(
        id="job-1",
        title="Junior Data Analyst",
        description="Analyze datasets and communicate findings.",
        required_skills=("Python", "SQL"),
        location="Remote",
        application_url="https://jobs.example.invalid/apply",
        source="Synthetic fixture",
        updated_at=datetime.now(UTC).date(),
    )
