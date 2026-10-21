"""Deterministic resume readability and ATS-oriented checks."""

import re
from dataclasses import dataclass

from models.job import Job


@dataclass(frozen=True, slots=True)
class ResumeQualityFinding:
    title: str
    status: str
    detail: str
    suggestion: str


@dataclass(frozen=True, slots=True)
class ResumeQualityReport:
    findings: tuple[ResumeQualityFinding, ...]
    compared_listing_count: int


_SECTION_ALIASES = {
    "Experience": (
        "experience",
        "work experience",
        "employment",
        "professional experience",
        "work history",
    ),
    "Education": ("education", "academic background", "academic qualifications"),
    "Skills": ("skills", "technical skills", "core competencies", "expertise"),
}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", " ", value.casefold()).strip()


def _heading_lines(text: str) -> set[str]:
    headings: set[str] = set()
    for line in text.splitlines():
        cleaned = re.sub(r"^[\s•*\-–—]+|[\s:|]+$", "", line).strip()
        if cleaned and len(cleaned) <= 80:
            headings.add(_normalize(cleaned))
    return headings


class ResumeQualityService:
    """Flag common parse and structure concerns without producing an ATS score."""

    def evaluate(
        self,
        resume_text: str,
        relevant_jobs: list[Job] | None = None,
        career_stage: str = "",
    ) -> ResumeQualityReport:
        jobs = relevant_jobs or []
        findings = [
            self._readability_finding(resume_text),
            self._section_finding(resume_text),
            self._impact_finding(resume_text),
            self._keyword_finding(resume_text, jobs),
        ]
        if career_stage.casefold() in {"student", "fresher"}:
            findings.append(self._project_section_finding(resume_text))
        return ResumeQualityReport(tuple(findings), len(jobs))

    @staticmethod
    def _readability_finding(text: str) -> ResumeQualityFinding:
        replacement_count = text.count("\ufffd")
        control_count = sum(ord(char) < 32 and char not in "\n\r\t" for char in text)
        if len(text.strip()) < 200 or replacement_count or control_count:
            reasons = []
            if len(text.strip()) < 200:
                reasons.append("very little text was extracted")
            if replacement_count:
                reasons.append(f"{replacement_count} unreadable character(s) were detected")
            if control_count:
                reasons.append("unexpected control characters were detected")
            return ResumeQualityFinding(
                "Extracted text readability",
                "Review",
                "The parser found " + " and ".join(reasons) + ".",
                "Check the original file, use a text-based PDF or DOCX, or paste the resume text.",
            )
        return ResumeQualityFinding(
            "Extracted text readability",
            "Looks readable",
            "Text was extracted without obvious encoding errors.",
            "Review the extracted content for layout or ordering issues before relying on it.",
        )

    @staticmethod
    def _section_finding(text: str) -> ResumeQualityFinding:
        headings = _heading_lines(text)
        missing = [
            section
            for section, aliases in _SECTION_ALIASES.items()
            if not any(_normalize(alias) in headings for alias in aliases)
        ]
        if not missing:
            return ResumeQualityFinding(
                "Common section headings",
                "Looks clear",
                "Recognizable experience, education, skills, and projects headings were found.",
                "Keep headings concise and conventional so people and parsing software can locate sections.",
            )
        return ResumeQualityFinding(
            "Common section headings",
            "Review",
            "Could not identify clear headings for: " + ", ".join(missing) + ".",
            "Add conventional headings for relevant sections. A section may exist under a different name.",
        )

    @staticmethod
    def _impact_finding(text: str) -> ResumeQualityFinding:
        bullet_lines = [
            line.strip()
            for line in text.splitlines()
            if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)
        ]
        has_metrics = any(re.search(r"\b\d+(?:[.,]\d+)?%?\b", line) for line in bullet_lines)
        if bullet_lines and has_metrics:
            return ResumeQualityFinding(
                "Evidence of outcomes",
                "Found",
                "Some bullet points include measurable details.",
                "Ensure each figure is accurate and provide context for important outcomes.",
            )
        return ResumeQualityFinding(
            "Evidence of outcomes",
            "Optional improvement",
            "The extracted resume does not show measurable outcomes in its bullet points.",
            "Where truthful, describe results with scope, scale, time saved, quality, or other measurable outcomes.",
        )

    @staticmethod
    def _project_section_finding(text: str) -> ResumeQualityFinding:
        if any(
            _normalize(alias) in _heading_lines(text)
            for alias in ("projects", "project experience", "selected projects")
        ):
            return ResumeQualityFinding(
                "Projects and practical work",
                "Found",
                "A projects section was identified, which can help show practical experience.",
                "Include truthful coursework, internships, hackathons, or open-source examples where relevant.",
            )
        return ResumeQualityFinding(
            "Projects and practical work",
            "Optional improvement",
            "No clear projects section was identified. This can be useful for students and freshers.",
            "Consider adding relevant coursework, projects, internships, hackathons, or open-source work with specific contributions.",
        )

    @staticmethod
    def _keyword_finding(text: str, jobs: list[Job]) -> ResumeQualityFinding:
        requirements: dict[str, str] = {}
        for job in jobs:
            for skill in job.required_skills:
                normalized = _normalize(skill)
                if normalized:
                    requirements.setdefault(normalized, skill)
        source = _normalize(text)
        missing = [
            display
            for normalized, display in requirements.items()
            if not re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", source)
        ]
        if not jobs or not requirements:
            reason = (
                "No current selected job listings were available for a role-keyword comparison."
                if not jobs
                else "The selected current listings did not contain extractable skill terms."
            )
            return ResumeQualityFinding(
                "Role keywords",
                "Not assessed",
                reason,
                "Choose a target role or review current listings to see relevant terms.",
            )
        if not missing:
            return ResumeQualityFinding(
                "Role keywords",
                "Found",
                "The selected listings' extracted skill terms appear in the resume text.",
                "Use only keywords that accurately describe your experience.",
            )
        return ResumeQualityFinding(
            "Role keywords",
            "Review",
            "These selected-listing skill terms were not found in the resume text: "
            + ", ".join(missing[:8])
            + (" and others." if len(missing) > 8 else "."),
            "If you have these skills, consider adding truthful evidence. Their absence from the resume does not prove you lack them.",
        )
