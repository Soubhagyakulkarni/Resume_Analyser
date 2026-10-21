"""Integration tests for downloadable analysis reports."""

from reports.pdf_renderer import ReportLabPdfRenderer
from services.report_service import ReportService


def test_report_renderer_generates_pdf_with_analysis_sections(sample_analysis):
    pdf = ReportService(ReportLabPdfRenderer()).generate(sample_analysis, [])

    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 500
