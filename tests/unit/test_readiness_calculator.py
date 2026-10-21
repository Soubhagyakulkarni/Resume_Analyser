"""Unit tests for calculate_readiness()."""

from services.career_profile import calculate_readiness
from services.resume_quality_service import ResumeQualityFinding, ResumeQualityReport


def _report(*statuses: str) -> ResumeQualityReport:
    """Build a synthetic quality report with the given statuses."""
    findings = tuple(
        ResumeQualityFinding(
            title=f"Check {i}",
            status=status,
            detail="detail",
            suggestion="suggestion",
        )
        for i, status in enumerate(statuses)
    )
    return ResumeQualityReport(findings=findings, compared_listing_count=0)


class TestCalculateReadiness:
    def test_none_report_returns_developing(self):
        assert calculate_readiness(None) == "Developing"

    def test_zero_review_findings_returns_strong(self):
        report = _report("Looks readable", "Looks clear", "Found", "Found")
        assert calculate_readiness(report) == "Strong"

    def test_one_review_finding_returns_good(self):
        report = _report("Looks readable", "Review", "Found", "Found")
        assert calculate_readiness(report) == "Good"

    def test_two_review_findings_returns_developing(self):
        report = _report("Review", "Review", "Found", "Found")
        assert calculate_readiness(report) == "Developing"

    def test_three_review_findings_returns_low(self):
        report = _report("Review", "Review", "Review", "Found")
        assert calculate_readiness(report) == "Low"

    def test_optional_improvement_counts_as_review(self):
        report = _report("Optional improvement", "Looks readable", "Found", "Found")
        assert calculate_readiness(report) == "Good"

    def test_empty_findings_returns_strong(self):
        report = _report()
        assert calculate_readiness(report) == "Strong"
