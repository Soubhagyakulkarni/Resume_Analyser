"""Tests for role-linked skill-development planning."""

from dataclasses import replace

import pytest

from services.skill_development_service import (
    LearningResource,
    SkillDevelopmentService,
)


def test_plan_prioritizes_skills_shared_across_jobs(sample_analysis, sample_job):
    second_job = replace(
        sample_job,
        id="job-2",
        title="Graduate Backend Developer",
        required_skills=("SQL",),
    )
    first_job = replace(sample_job, required_skills=("SQL", "Docker"))

    plan = SkillDevelopmentService().build_plan(sample_analysis, [first_job, second_job])

    assert [step.skill for step in plan] == ["SQL", "Docker"]
    assert plan[0].listing_count == 2
    assert plan[0].roles == ("Junior Data Analyst", "Graduate Backend Developer")
    assert plan[0].resource is not None
    assert plan[0].resource.url.startswith("https://")


def test_plan_excludes_skills_in_analysis_or_resume_text(sample_analysis, sample_job):
    job = replace(sample_job, required_skills=("Python", "SQL"))

    plan = SkillDevelopmentService().build_plan(
        sample_analysis,
        [job],
        resume_text="Built solutions with SQL over several projects.",
    )

    assert plan == []


def test_unmapped_skill_has_no_fabricated_learning_link(sample_analysis, sample_job):
    job = replace(sample_job, required_skills=("Kubernetes",))

    plan = SkillDevelopmentService().build_plan(sample_analysis, [job])

    assert len(plan) == 1
    assert plan[0].skill == "Kubernetes"
    assert plan[0].resource is None


def test_learning_resource_rejects_non_https_urls():
    with pytest.raises(ValueError, match="HTTPS"):
        LearningResource("Untrusted", "Example", "http://example.com/course")


def test_empty_job_list_returns_no_steps(sample_analysis):
    assert SkillDevelopmentService().build_plan(sample_analysis, []) == []


def test_plan_limit_must_be_positive(sample_analysis):
    with pytest.raises(ValueError, match="positive"):
        SkillDevelopmentService().build_plan(sample_analysis, [], limit=0)
