"""Role-linked skill-development steps with a small curated resource registry."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from models.analysis import ResumeAnalysis
from models.job import Job


@dataclass(frozen=True, slots=True)
class LearningResource:
    title: str
    provider: str
    url: str

    def __post_init__(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Learning resource URLs must use HTTPS")


@dataclass(frozen=True, slots=True)
class SkillDevelopmentStep:
    skill: str
    roles: tuple[str, ...]
    listing_count: int
    resource: LearningResource | None


_RESOURCES = {
    "python": LearningResource(
        "The Python Tutorial",
        "Python documentation",
        "https://docs.python.org/3/tutorial/",
    ),
    "sql": LearningResource(
        "Query and modify data with Transact-SQL",
        "Microsoft Learn",
        "https://learn.microsoft.com/en-us/training/paths/get-started-querying-with-transact-sql/",
    ),
    "javascript": LearningResource(
        "JavaScript Guide",
        "MDN Web Docs",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
    ),
    "react": LearningResource(
        "Quick Start",
        "React documentation",
        "https://react.dev/learn",
    ),
    "git": LearningResource(
        "Git Tutorial",
        "Git documentation",
        "https://git-scm.com/docs/gittutorial",
    ),
    "docker": LearningResource(
        "Get started",
        "Docker documentation",
        "https://docs.docker.com/get-started/",
    ),
    "machine learning": LearningResource(
        "Machine Learning Crash Course",
        "Google for Developers",
        "https://developers.google.com/machine-learning/crash-course",
    ),
    "html": LearningResource(
        "Learn web development",
        "MDN Web Docs",
        "https://developer.mozilla.org/en-US/docs/Learn_web_development",
    ),
    "css": LearningResource(
        "Learn web development",
        "MDN Web Docs",
        "https://developer.mozilla.org/en-US/docs/Learn_web_development",
    ),
}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", " ", value.casefold()).strip()


class SkillDevelopmentService:
    """Prioritize resume-unlisted skills shared by the current job listings."""

    def build_plan(
        self,
        analysis: ResumeAnalysis,
        jobs: list[Job],
        limit: int = 6,
        resume_text: str = "",
    ) -> list[SkillDevelopmentStep]:
        if limit < 1:
            raise ValueError("limit must be positive")

        resume_skills = {_normalize(skill.name) for skill in analysis.skills}
        normalized_resume = _normalize(resume_text)
        opportunities: dict[str, tuple[str, list[str], set[str]]] = {}
        for job in jobs:
            for skill in job.required_skills:
                normalized = _normalize(skill)
                if (
                    not normalized
                    or normalized in resume_skills
                    or _contains_phrase(normalized_resume, normalized)
                ):
                    continue
                if normalized not in opportunities:
                    opportunities[normalized] = (skill, [], set())
                _, roles, listing_ids = opportunities[normalized]
                listing_ids.add(job.id)
                if job.title not in roles:
                    roles.append(job.title)

        sorted_opportunities = sorted(
            opportunities.values(),
            key=lambda item: (-len(item[2]), item[0].casefold()),
        )
        plan: list[SkillDevelopmentStep] = []
        for skill, roles, listing_ids in sorted_opportunities[:limit]:
            plan.append(
                SkillDevelopmentStep(
                    skill=skill,
                    roles=tuple(roles[:4]),
                    listing_count=len(listing_ids),
                    resource=_RESOURCES.get(_normalize(skill)),
                )
            )
        return plan


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(
        text and phrase and re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text)
    )
