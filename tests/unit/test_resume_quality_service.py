"""Tests for deterministic resume readability and ATS-oriented checks."""

from dataclasses import replace

from services.resume_quality_service import ResumeQualityService


def _finding(report, title):
    return next(item for item in report.findings if item.title == title)


def test_reports_short_or_unreadable_extracted_text():
    service = ResumeQualityService()

    short = service.evaluate("Short resume")
    unreadable = service.evaluate(("Resume " * 40) + "\ufffd")

    assert _finding(short, "Extracted text readability").status == "Review"
    assert "unreadable character" in _finding(unreadable, "Extracted text readability").detail


def test_reports_unexpected_control_characters():
    resume = ("Readable resume content " * 12) + "\x01"

    finding = _finding(ResumeQualityService().evaluate(resume), "Extracted text readability")

    assert finding.status == "Review"
    assert "control characters" in finding.detail


def test_reports_common_missing_sections():
    report = ResumeQualityService().evaluate("A" * 250)

    finding = _finding(report, "Common section headings")
    assert finding.status == "Review"
    assert "Experience" in finding.detail
    assert "Education" in finding.detail


def test_recognizes_common_section_headings_and_metrics():
    resume = "\n".join(
        [
            "Professional Experience",
            "- Improved page load time by 25%",
            "Education",
            "Technical Skills",
            "Projects",
        ]
        + ["Additional resume content"] * 30
    )

    report = ResumeQualityService().evaluate(resume)

    assert _finding(report, "Common section headings").status == "Looks clear"
    assert _finding(report, "Evidence of outcomes").status == "Found"


def test_suggests_truthful_metrics_when_no_bullet_outcomes():
    resume = "\n".join(["Experience", "Worked on projects"] + ["Resume content"] * 30)

    finding = _finding(ResumeQualityService().evaluate(resume), "Evidence of outcomes")

    assert finding.status == "Optional improvement"
    assert "truthful" in finding.suggestion


def test_keyword_check_distinguishes_found_missing_and_unassessed(sample_job):
    service = ResumeQualityService()
    role = replace(sample_job, required_skills=("Python", "SQL"))

    present = service.evaluate("Experienced in Python and SQL.", [role])
    missing = service.evaluate("Experienced in Python only.", [role])
    unassessed = service.evaluate("Experienced in Python only.")

    assert _finding(present, "Role keywords").status == "Found"
    assert "SQL" in _finding(missing, "Role keywords").detail
    assert _finding(missing, "Role keywords").status == "Review"
    assert _finding(unassessed, "Role keywords").status == "Not assessed"
    assert unassessed.compared_listing_count == 0


def test_keyword_check_is_not_assessed_when_listings_have_no_skills(sample_job):
    job_without_skills = replace(sample_job, required_skills=())

    report = ResumeQualityService().evaluate("Resume content", [job_without_skills])

    finding = _finding(report, "Role keywords")
    assert finding.status == "Not assessed"
    assert "did not contain extractable skill terms" in finding.detail


def test_project_section_check_is_contextual_to_students_and_freshers():
    service = ResumeQualityService()
    resume = "\n".join(["Experience", "Education", "Skills"] + ["Resume detail"] * 30)

    professional = service.evaluate(resume, career_stage="Experienced")
    student = service.evaluate(resume, career_stage="Student")
    student_with_projects = service.evaluate(
        resume + "\nProjects\nBuilt a portfolio site", career_stage="Fresher"
    )

    assert all(f.title != "Projects and practical work" for f in professional.findings)
    assert _finding(student, "Projects and practical work").status == "Optional improvement"
    assert _finding(student_with_projects, "Projects and practical work").status == "Found"
