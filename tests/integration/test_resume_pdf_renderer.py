from io import BytesIO

from pypdf import PdfReader

from reports.resume_pdf_renderer import ResumePdfRenderer


def test_resume_renderer_returns_pdf_for_user_provided_sections():
    pdf = ResumePdfRenderer().render(
        "Asha Student",
        "asha@example.com  |  Pune",
        [("Education", "BSc Computer Science"), ("Projects", "Built a study planner")],
    )

    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 500
    extracted = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)
    assert "Asha Student" in extracted
    assert "BSc Computer Science" in extracted


def test_resume_renderer_safely_escapes_markup_in_user_content():
    pdf = ResumePdfRenderer().render(
        "<Asha>",
        "",
        [("Projects", "Built <script>safe & useful</script> app")],
    )

    assert pdf.startswith(b"%PDF-")


def test_resume_renderer_supports_named_layouts_and_target_role():
    for template in ("Classic", "Modern", "Compact"):
        pdf = ResumePdfRenderer().render(
            "Asha Student",
            "asha@example.com",
            [("Projects", "Built a study planner")],
            template=template,
            subtitle="Junior Data Analyst",
        )
        extracted = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)

        assert pdf.startswith(b"%PDF-")
        assert "Junior Data Analyst" in extracted
        assert "Built a study planner" in extracted


def test_resume_pdf_preserves_builder_section_order():
    pdf = ResumePdfRenderer().render(
        "Asha Student",
        "asha@example.com",
        [
            ("Profile", "Computer science graduate."),
            ("Experience", "Volunteer tutor."),
            ("Projects", "Built a study planner."),
            ("Education", "BSc Computer Science."),
            ("Skills", "Python, SQL."),
        ],
        template="Modern",
    )
    extracted = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)

    assert extracted.index("Projects") < extracted.index("Education")


def test_resume_pdf_keeps_entry_details_in_readable_single_column_text():
    pdf = ResumePdfRenderer().render(
        "Asha Student",
        "asha@example.com | Pune",
        [
            (
                "Experience",
                (
                    "Data Analyst Intern | Example Co | Jun 2024 - Aug 2024\n"
                    "• Analyzed 1,200 records and reduced manual reporting by 20%"
                ),
            )
        ],
    )
    extracted = " ".join(
        page.extract_text() for page in PdfReader(BytesIO(pdf)).pages
    )

    assert "Data Analyst Intern | Example Co | Jun 2024 - Aug 2024" in extracted
    assert "- Analyzed 1,200 records and reduced manual reporting by 20%" in extracted
