from services.resume_builder_service import (
    ResumeDraft,
    build_contact_line,
    build_resume_sections,
    review_resume_draft,
    split_existing_resume,
)


def test_build_resume_sections_includes_only_user_provided_content():
    draft = ResumeDraft(
        full_name="Sam Student",
        education="BSc Computer Science\nUniversity",
        projects="Built a class project",
    )

    assert build_resume_sections(draft) == [
        ("Education", "BSc Computer Science\nUniversity"),
        ("Projects", "Built a class project"),
    ]


def test_resume_sections_follow_fresher_resume_sequence():
    draft = ResumeDraft(
        summary="Focused computer science student.",
        experience="Volunteer tutor",
        projects="Built a study planner",
        education="BSc Computer Science",
        skills="Python, SQL",
        certifications="Introductory SQL certificate",
    )

    assert [heading for heading, _ in build_resume_sections(draft)] == [
        "Profile",
        "Education",
        "Experience",
        "Projects",
        "Skills",
        "Certifications",
    ]


def test_build_contact_line_omits_blank_optional_fields():
    draft = ResumeDraft(email=" sam@example.com ", location="Pune")

    assert build_contact_line(draft) == "sam@example.com  |  Pune"


def test_build_contact_line_includes_optional_portfolio_links():
    draft = ResumeDraft(
        email="sam@example.com",
        linkedin="https://linkedin.example/sam",
        portfolio="https://portfolio.example/sam",
    )

    assert build_contact_line(draft) == (
        "sam@example.com  |  https://linkedin.example/sam  |  https://portfolio.example/sam"
    )


def test_resume_review_reports_completeness_without_inventing_data():
    completeness, checks = review_resume_draft(
        ResumeDraft(
            full_name="Sam Student",
            email="sam@example.com",
            summary=(
                "Computer science student focused on data analysis and practical projects, "
                "with experience building useful dashboards and collaborating with peers "
                "to solve practical problems for campus organizations."
            ),
            education="BSc Computer Science, University, 2026",
            skills="Python, SQL",
            projects="Built a dashboard used by 20 students",
        )
    )

    assert completeness == 100
    assert all(status == "Complete" for _, status, _ in checks)


def test_resume_review_identifies_missing_sections_and_impact():
    completeness, checks = review_resume_draft(ResumeDraft(full_name="Sam Student"))

    assert completeness == 0
    assert {status for _, status, _ in checks} == {"Add detail", "Consider"}


def test_resume_review_does_not_treat_years_as_measurable_impact():
    _, checks = review_resume_draft(
        ResumeDraft(
            education="BSc Computer Science, University, 2026",
            projects="Built a dashboard during 2025.",
        )
    )

    impact_check = next(check for check in checks if check[0] == "Impact")
    assert impact_check[1] == "Consider"


def test_split_existing_resume_keeps_text_and_omits_blank_content():
    assert split_existing_resume("  Education\nDegree\n\nProjects\nApp  ") == [
        ("Education", "Degree"),
        ("Projects", "App"),
    ]
    assert split_existing_resume("Just plain text without headings") == [
        ("Resume content", "Just plain text without headings")
    ]
    assert split_existing_resume(" \n ") == []
