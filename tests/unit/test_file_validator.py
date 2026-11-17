"""Tests for secure upload validation."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.services.resume_service import ResumeService
from app.utils.errors import InvalidResumeError
from parsers.file_validator import validate_resume_file


def test_accepts_pdf_signature():
    assert validate_resume_file("resume.pdf", b"%PDF-1.4\nsample", 100) == "pdf"


def test_rejects_extension_signature_mismatch():
    with pytest.raises(InvalidResumeError):
        validate_resume_file("resume.pdf", b"not a pdf", 100)


def test_rejects_oversized_file():
    with pytest.raises(InvalidResumeError):
        validate_resume_file("resume.pdf", b"%PDF-1.4\nsample", 5)


def test_accepts_docx_container_with_main_document():
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "<document/>")
    assert validate_resume_file("resume.docx", output.getvalue(), 1000) == "docx"


def test_rejects_invalid_docx_container():
    with pytest.raises(InvalidResumeError):
        validate_resume_file("resume.docx", b"not a zip file", 100)


def test_resume_service_accepts_pasted_text():
    parsed = ResumeService(1000, 100).parse_text("  Python developer  ")
    assert parsed.file_type == "text"
    assert parsed.text == "Python developer"


def test_resume_service_rejects_oversized_pasted_text():
    with pytest.raises(InvalidResumeError):
        ResumeService(1000, 5).parse_text("too much text")


def test_resume_service_extracts_synthetic_pdf_text():
    from pathlib import Path

    fixture = Path(__file__).parents[1] / "fixtures" / "sample_resume.pdf"
    parsed = ResumeService(100_000, 1000).parse(fixture.name, fixture.read_bytes())
    assert "Python data project" in parsed.text


def test_resume_service_extracts_synthetic_docx_text():
    from pathlib import Path

    fixture = Path(__file__).parents[1] / "fixtures" / "sample_resume.docx"
    parsed = ResumeService(100_000, 1000).parse(fixture.name, fixture.read_bytes())
    assert "Python data project" in parsed.text
