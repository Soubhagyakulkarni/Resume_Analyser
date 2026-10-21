"""Tests for adding career planning and resume checks to downloadable reports."""

from services.career_profile import CareerProfile
from services.report_service import ReportService
from services.resume_quality_service import ResumeQualityService
from services.skill_development_service import (
    LearningResource,
    SkillDevelopmentStep,
)


class RecordingPdfRenderer:
    def __init__(self):
        self.sections = None

    def render(self, title, sections):
        self.sections = sections
        return b"synthetic pdf"


def test_report_includes_optional_skill_plan_and_resume_quality(sample_analysis, sample_job):
    renderer = RecordingPdfRenderer()
    service = ReportService(renderer)
    plan = [
        SkillDevelopmentStep(
            skill="SQL",
            roles=(sample_job.title,),
            listing_count=1,
            resource=LearningResource(
                "SQL Basics",
                "Microsoft Learn",
                "https://learn.microsoft.com/sql/",
            ),
        )
    ]
    quality = ResumeQualityService().evaluate("Experience\\nPython and SQL")

    profile = CareerProfile(stage="Student", goal="Internship")
    assert (
        service.generate(sample_analysis, [], plan, quality, career_profile=profile)
        == b"synthetic pdf"
    )

    sections = dict(renderer.sections)
    assert "Career stage: Student" in sections["Report information"]
    assert "Primary goal: Internship" in sections["Report information"]
    assert "SQL" in sections["Role-linked skill development plan"][0]
    assert "https://learn.microsoft.com/sql/" in sections["Role-linked skill development plan"][0]
    assert sections["ATS-friendly resume checks (not an ATS score)"]
