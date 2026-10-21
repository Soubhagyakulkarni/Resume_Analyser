"""Report assembly independent from the Streamlit presentation."""

from __future__ import annotations

from datetime import UTC, datetime

from reportlab.platypus.doctemplate import LayoutError

from app.utils.errors import ReportGenerationError
from models.analysis import ResumeAnalysis
from models.job import JobRecommendation
from services.career_profile import CareerProfile, calculate_readiness
from services.ports import PdfRenderer
from services.resume_quality_service import ResumeQualityReport
from services.skill_development_service import SkillDevelopmentStep


class ReportService:
    def __init__(self, renderer: PdfRenderer) -> None:
        self._renderer = renderer

    def generate(
        self,
        analysis: ResumeAnalysis,
        recommendations: list[JobRecommendation],
        skill_plan: list[SkillDevelopmentStep] | None = None,
        quality_report: ResumeQualityReport | None = None,
        career_profile: CareerProfile | None = None,
    ) -> bytes:
        today = datetime.now(UTC).date().isoformat()
        sections: list[tuple[str, list[str]]] = []

        # ── Cover / header info ────────────────────────────────────────────────
        header_lines = [f"Report generated: {today}"]
        if career_profile and career_profile.is_set:
            if career_profile.stage:
                header_lines.append(f"Career stage: {career_profile.stage}")
            if career_profile.goal:
                header_lines.append(f"Primary goal: {career_profile.goal}")
            if career_profile.preferred_role:
                header_lines.append(f"Preferred role/field: {career_profile.preferred_role}")
            if career_profile.preferred_location:
                header_lines.append(f"Preferred location: {career_profile.preferred_location}")
        sections.append(("Report information", header_lines))

        # ── Readiness summary ─────────────────────────────────────────────────
        if quality_report is not None:
            readiness = calculate_readiness(quality_report)
        else:
            readiness = "Not assessed"
        sections.append(
            (
                "Resume readiness",
                [
                    f"Overall readiness level: {readiness}",
                    (
                        "This is derived from structural and keyword quality checks only."
                        " It is not an ATS score or hiring prediction."
                    ),
                ],
            )
        )

        # ── AI-generated summary ─────────────────────────────────────────────
        sections.append(("Resume summary (AI-generated)", [analysis.summary or "Not available."]))

        # ── Top strengths (experience highlights) ────────────────────────────
        sections.append(
            (
                "Top strengths",
                list(analysis.experience_highlights) or ["Not available."],
            )
        )

        # ── Technical & soft skills ──────────────────────────────────────────
        sections.append(
            (
                "Technical skills",
                [
                    f"{skill.name} ({'inferred' if skill.inferred else 'stated'})"
                    f"; evidence: {skill.evidence or 'not specified'}"
                    for skill in analysis.technical_skills
                ]
                or ["Not available."],
            )
        )
        sections.append(
            (
                "Soft skills",
                [
                    f"{skill.name} ({'inferred' if skill.inferred else 'stated'})"
                    f"; evidence: {skill.evidence or 'not specified'}"
                    for skill in analysis.soft_skills
                ]
                or ["Not available."],
            )
        )

        # ── Experience assessment ─────────────────────────────────────────────
        sections.append(
            (
                "Experience assessment",
                [analysis.experience_assessment or "Not available."],
            )
        )

        # ── Improvement suggestions ───────────────────────────────────────────
        sections.append(
            (
                "Key improvement areas",
                [
                    f"[{item.priority.upper()}] {item.issue}: {item.recommendation}"
                    for item in analysis.suggestions
                ]
                or ["Not available."],
            )
        )

        # ── Top 5 job recommendations ─────────────────────────────────────────
        top_recs = recommendations[:5]
        sections.append(
            (
                "Top relevant job roles (up to 5)",
                [
                    f"{item.job.title}"
                    f" — {item.job.location or 'Location not listed'}"
                    f" ({item.match_ratio:.0%} skill overlap)"
                    f": {item.rationale}"
                    f" Apply: {item.job.application_url or 'Not listed'}"
                    for item in top_recs
                ]
                or ["No matched roles found in the current catalog."],
            )
        )

        # ── Missing skills ────────────────────────────────────────────────────
        all_missing = sorted(
            {skill for item in recommendations for skill in item.missing_from_resume}
        )
        sections.append(
            (
                "Skills to develop (not found in this resume)",
                all_missing or ["Not available."],
            )
        )

        # ── Skill development plan (keep legacy heading for backward compatibility) ──
        skill_plan_lines = [
            f"{step.skill}; appears in {step.listing_count} selected listing(s)"
            f"; related roles: {', '.join(step.roles) or 'current listings'}"
            + (
                f"; resource: {step.resource.title} ({step.resource.provider}) {step.resource.url}"
                if step.resource
                else "; no curated resource link available"
            )
            for step in (skill_plan or [])
        ] or ["Not available."]
        # Legacy heading retained so existing test assertions still pass.
        sections.append(("Role-linked skill development plan", skill_plan_lines))

        # ── Resume quality checks (keep legacy heading for backward compatibility) ─
        quality_lines = [
            f"{finding.status} — {finding.title}: {finding.detail} Suggestion: {finding.suggestion}"
            for finding in (quality_report.findings if quality_report else ())
        ] or ["Not available."]
        # Legacy heading retained so existing test assertions still pass.
        sections.append(("ATS-friendly resume checks (not an ATS score)", quality_lines))

        # ── Limitations ───────────────────────────────────────────────────────
        sections.append(
            (
                "Limitations and disclaimer",
                list(analysis.caveats)
                + [
                    (
                        "This report provides career guidance only. It is not an ATS score,"
                        " a hiring decision, or a job guarantee."
                    ),
                    "AI analysis depends on resume text quality and AI provider availability.",
                    "Job matches depend on catalog coverage and the 30-day freshness window.",
                    "The app does not verify external profiles, repositories, or actual abilities.",
                    "No match does not mean the resume is poor or the candidate is unsuitable.",
                ],
            )
        )

        try:
            return self._renderer.render("AI Resume Analysis", sections)
        except (LayoutError, OSError, ValueError, RuntimeError) as exc:
            raise ReportGenerationError() from exc
