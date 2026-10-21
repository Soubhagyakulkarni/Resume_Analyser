"""Career profile personalization, readiness scoring, and next-action generation.

All functions are deterministic and free of I/O so they can be unit-tested
without mocks or live service calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from models.analysis import ResumeAnalysis
from models.job import JobRecommendation
from services.resume_quality_service import ResumeQualityReport
from services.skill_development_service import SkillDevelopmentStep

# ---------------------------------------------------------------------------
# Career profile
# ---------------------------------------------------------------------------

CareerStage = Literal["Student", "Fresher", "Early-career", "Experienced", ""]
PrimaryGoal = Literal["Internship", "First job", "Career switch", "Upskilling", ""]


@dataclass(frozen=True, slots=True)
class CareerProfile:
    """Optional, session-only career personalization.  All fields are optional."""

    stage: CareerStage = ""
    goal: PrimaryGoal = ""
    preferred_role: str = ""
    preferred_location: str = ""

    @property
    def is_set(self) -> bool:
        """Return True when the user provided at least one preference."""
        return bool(self.stage or self.goal or self.preferred_role or self.preferred_location)

    def framing_tag(self) -> str:
        """Return a short human-readable descriptor used for result-page headings."""
        if self.stage == "Student" or self.goal == "Internship":
            return "student"
        if self.stage == "Fresher" or self.goal == "First job":
            return "fresher"
        if self.goal == "Career switch":
            return "career-switcher"
        if self.stage == "Experienced" or self.goal == "Upskilling":
            return "experienced"
        return "general"

    def emphasis_note(self) -> str:
        """Return a tailored emphasis caption for the results page."""
        tag = self.framing_tag()
        if tag == "student":
            return (
                "Focused on projects, coursework, internships, hackathons, open-source work,"
                " and measurable impact — the signals that matter most for students."
            )
        if tag == "fresher":
            return (
                "Highlighting transferable skills, personal and academic projects, readiness"
                " indicators, and entry-level role alignment."
            )
        if tag == "career-switcher":
            return (
                "Emphasising transferable experience, adjacent skills, and realistic"
                " transition paths into your target field."
            )
        if tag == "experienced":
            return (
                "Focused on seniority alignment, specialisation depth, and advanced"
                " skill gaps relative to senior listings."
            )
        return "Providing general career guidance based on your resume content."


# ---------------------------------------------------------------------------
# Resume readiness
# ---------------------------------------------------------------------------

ReadinessLevel = Literal["Low", "Developing", "Good", "Strong"]


def calculate_readiness(quality_report: ResumeQualityReport | None) -> ReadinessLevel:
    """Derive a four-level readiness label from existing quality findings.

    Mapping (deterministic, no AI calls):
    - 0 "Review" findings  → Strong
    - 1 "Review" finding   → Good
    - 2 "Review" findings  → Developing
    - 3+ "Review" findings → Low
    """
    if quality_report is None:
        return "Developing"
    review_count = sum(
        1 for f in quality_report.findings if f.status.lower() in {"review", "optional improvement"}
    )
    if review_count == 0:
        return "Strong"
    if review_count == 1:
        return "Good"
    if review_count == 2:
        return "Developing"
    return "Low"


# ---------------------------------------------------------------------------
# Match strength
# ---------------------------------------------------------------------------

MatchStrength = Literal["Strong", "Moderate", "Exploratory"]
JobSortOrder = Literal["Relevance", "Newest", "Location"]


def classify_match_strength(match_ratio: float) -> MatchStrength:
    """Map a numeric match ratio to a human-readable strength label.

    Thresholds:
    - ≥ 0.70 → Strong
    - ≥ 0.40 → Moderate
    - <  0.40 → Exploratory
    """
    if match_ratio >= 0.70:
        return "Strong"
    if match_ratio >= 0.40:
        return "Moderate"
    return "Exploratory"


def sort_job_recommendations(
    recommendations: list[JobRecommendation],
    order: JobSortOrder = "Relevance",
) -> list[JobRecommendation]:
    """Return a sorted copy of recommendations without changing the input."""
    if order == "Newest":
        key = lambda item: (-item.job.updated_at.toordinal(), -item.match_ratio)
    elif order == "Location":
        key = lambda item: (item.job.location.casefold(), -item.match_ratio)
    elif order == "Relevance":
        key = lambda item: (-item.match_ratio, item.job.title.casefold())
    else:
        raise ValueError(f"Unsupported job sort order: {order}")
    return sorted(recommendations, key=key)


# ---------------------------------------------------------------------------
# Skill tier grouping
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SkillTier:
    """A named group of skill-development steps."""

    label: Literal["Start now", "Next", "Optional"]
    steps: tuple[SkillDevelopmentStep, ...]


def group_skill_tiers(plan: list[SkillDevelopmentStep]) -> list[SkillTier]:
    """Group a flat skill-development plan into three priority tiers.

    Tier assignment (deterministic):
    - listing_count ≥ 3  → Start now
    - listing_count == 2 → Next
    - listing_count == 1 → Optional
    """
    start_now: list[SkillDevelopmentStep] = []
    next_tier: list[SkillDevelopmentStep] = []
    optional: list[SkillDevelopmentStep] = []
    for step in plan:
        if step.listing_count >= 3:
            start_now.append(step)
        elif step.listing_count == 2:
            next_tier.append(step)
        else:
            optional.append(step)
    tiers: list[SkillTier] = []
    if start_now:
        tiers.append(SkillTier("Start now", tuple(start_now)))
    if next_tier:
        tiers.append(SkillTier("Next", tuple(next_tier)))
    if optional:
        tiers.append(SkillTier("Optional", tuple(optional)))
    return tiers


# ---------------------------------------------------------------------------
# Next-action generation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NextAction:
    """A single prioritised career action derived from existing analysis outputs."""

    title: str
    explanation: str
    priority: Literal["High", "Medium", "Low"]
    section: str  # human-readable label for the target section


def generate_next_actions(
    analysis: ResumeAnalysis,
    recommendations: list[JobRecommendation],
    skill_plan: list[SkillDevelopmentStep],
    quality_report: ResumeQualityReport | None,
    max_actions: int = 3,
) -> list[NextAction]:
    """Generate up to *max_actions* prioritised next actions.

    Sources (in priority order):
    1. High-priority improvement suggestions from AI analysis
    2. Missing skills from top job recommendations
    3. Top skill-development plan step
    4. Quality-check "Review" findings
    5. Explore job categories (fallback)

    All inputs come from existing analysis outputs — nothing is invented.
    """
    actions: list[NextAction] = []

    # 1. High-priority AI improvement suggestion
    high_suggestions = [s for s in analysis.suggestions if s.priority.lower() == "high"]
    if high_suggestions and len(actions) < max_actions:
        s = high_suggestions[0]
        actions.append(
            NextAction(
                title=s.issue,
                explanation=s.recommendation[:120] + ("…" if len(s.recommendation) > 120 else ""),
                priority="High",
                section="Resume Insights",
            )
        )

    # 2. Missing skills from the top recommendation
    if recommendations and len(actions) < max_actions:
        top = recommendations[0]
        if top.missing_from_resume:
            missing_list = ", ".join(top.missing_from_resume[:3])
            actions.append(
                NextAction(
                    title=f"Add missing skills for {top.job.title}",
                    explanation=(
                        f"Your resume didn't show evidence of: {missing_list}."
                        " If you have these skills, add truthful examples."
                    ),
                    priority="High",
                    section="Job Recommendations",
                )
            )

    # 3. Top skill from the development plan
    if skill_plan and len(actions) < max_actions:
        step = skill_plan[0]
        roles_label = ", ".join(step.roles[:2]) if step.roles else "current listings"
        actions.append(
            NextAction(
                title=f"Learn {step.skill}",
                explanation=(
                    f"Appears in {step.listing_count} selected listing(s)"
                    f" — roles include {roles_label}."
                ),
                priority="High" if step.listing_count >= 3 else "Medium",
                section="Skill Development Plan",
            )
        )

    # 4. First "Review" quality finding
    if quality_report and len(actions) < max_actions:
        review_findings = [
            f
            for f in quality_report.findings
            if f.status.lower() in {"review", "optional improvement"}
        ]
        if review_findings:
            f = review_findings[0]
            actions.append(
                NextAction(
                    title=f"Fix: {f.title}",
                    explanation=f.suggestion[:120] + ("…" if len(f.suggestion) > 120 else ""),
                    priority="Medium",
                    section="Resume Quality Checks",
                )
            )

    # 5. Explore a job category if no recommendations matched
    if not recommendations and len(actions) < max_actions:
        actions.append(
            NextAction(
                title="Explore job listings",
                explanation=(
                    "No skill-based matches were found. Browse current listings"
                    " or try adjusting your role and location filters."
                ),
                priority="Low",
                section="Job Recommendations",
            )
        )

    return actions[:max_actions]


# ---------------------------------------------------------------------------
# Sample / demo resume
# ---------------------------------------------------------------------------

SAMPLE_RESUME_TEXT: str = (
    "=== DEMO RESUME — Synthetic data only, not a real person ===\n\n"
    "Priya Sharma\n"
    "priya.demo@example.invalid | github.com/priya-demo | Bengaluru, India\n\n"
    "EDUCATION\n"
    "B.E. Computer Science — Example University, 2024\n"
    "CGPA: 8.4/10 | Relevant coursework: Data Structures, DBMS, Machine Learning\n\n"
    "TECHNICAL SKILLS\n"
    "Languages: Python, JavaScript, SQL\n"
    "Frameworks: React, Flask\n"
    "Tools: Git, Docker (basic), VS Code\n\n"
    "PROJECTS\n"
    "Job Portal Scraper (Python, BeautifulSoup)\n"
    "- Scraped and normalised 2,000+ listings from three job boards\n"
    "- Reduced duplicate entries by 40% using fuzzy-string deduplication\n\n"
    "Expense Tracker Web App (React, Flask, SQLite)\n"
    "- Built a full-stack budgeting app; used by 12 classmates for 3 months\n"
    "- Implemented JWT authentication and responsive mobile layout\n\n"
    "INTERNSHIP\n"
    "Data Analyst Intern — TechStartup Pvt Ltd (Jun–Aug 2023)\n"
    "- Cleaned and analysed 50,000-row customer dataset in Pandas\n"
    "- Delivered weekly summary dashboards to product team using Matplotlib\n\n"
    "SOFT SKILLS\n"
    "Communication, Team collaboration, Problem-solving, Self-directed learning\n\n"
    "=== END DEMO RESUME ==="
)


# ---------------------------------------------------------------------------
# Weekly focus plan helper
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WeeklyFocusWeek:
    """One week in a simple four-week skill-building plan."""

    week: int
    theme: str
    actions: tuple[str, ...]


def build_weekly_focus(skill: str) -> list[WeeklyFocusWeek]:
    """Return a generic four-week skill-building plan for *skill*."""
    return [
        WeeklyFocusWeek(
            1,
            f"Learn {skill} fundamentals",
            (
                f"Study the official {skill} documentation or a beginner tutorial.",
                "Take notes on core concepts and write small practice exercises.",
            ),
        ),
        WeeklyFocusWeek(
            2,
            f"Build a small {skill} project",
            (
                f"Pick a mini-project that uses {skill} to solve a real problem.",
                "Commit code daily, even small increments, to build a visible trail.",
            ),
        ),
        WeeklyFocusWeek(
            3,
            "Document and add to your resume",
            (
                "Write a concise project description with measurable outcomes.",
                f"Add {skill} to your skills section with honest evidence.",
            ),
        ),
        WeeklyFocusWeek(
            4,
            "Apply to relevant listings",
            (
                f"Filter job listings that require {skill} and review their descriptions.",
                f"Tailor your cover note to highlight your new {skill} project.",
            ),
        ),
    ]
