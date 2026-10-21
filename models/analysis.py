"""Validated resume analysis result models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    evidence: str
    inferred: bool = False


@dataclass(frozen=True, slots=True)
class ImprovementSuggestion:
    priority: str
    issue: str
    recommendation: str
    evidence: str


@dataclass(frozen=True, slots=True)
class ResumeAnalysis:
    summary: str
    technical_skills: tuple[Skill, ...]
    soft_skills: tuple[Skill, ...]
    experience_assessment: str
    experience_highlights: tuple[str, ...]
    learning_suggestions: tuple[str, ...]
    resume_improvements: tuple[ImprovementSuggestion, ...]
    caveats: tuple[str, ...] = ()

    @property
    def skills(self) -> tuple[Skill, ...]:
        """Return both skill categories for matching and evidence checks."""
        return self.technical_skills + self.soft_skills

    @property
    def suggestions(self) -> tuple[ImprovementSuggestion, ...]:
        """Maintain the concise name used by report consumers."""
        return self.resume_improvements

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ResumeAnalysis":
        """Validate and bound untrusted structured model output."""
        required = {
            "summary",
            "technical_skills",
            "soft_skills",
            "experience_assessment",
            "experience_highlights",
            "learning_suggestions",
            "resume_improvements",
        }
        if not isinstance(payload, dict) or not required.issubset(payload):
            raise ValueError("Analysis response is missing required fields")

        summary = _bounded_text(payload["summary"], "summary", 4000)
        technical_value = payload["technical_skills"]
        soft_value = payload["soft_skills"]
        experience_assessment = _bounded_text(
            payload["experience_assessment"], "experience_assessment", 3000
        )
        experiences_value = payload["experience_highlights"]
        learning_value = payload["learning_suggestions"]
        suggestions_value = payload["resume_improvements"]
        caveats_value = payload.get("caveats", [])
        technical_skills = _parse_skills(technical_value, "technical_skills")
        soft_skills = _parse_skills(soft_value, "soft_skills")
        if not isinstance(experiences_value, list) or len(experiences_value) > 50:
            raise ValueError("experience_highlights must be a list with at most 50 entries")
        if not isinstance(learning_value, list) or len(learning_value) > 30:
            raise ValueError("learning_suggestions must be a list with at most 30 entries")
        if not isinstance(suggestions_value, list) or len(suggestions_value) > 50:
            raise ValueError("resume_improvements must be a list with at most 50 entries")
        if not isinstance(caveats_value, list) or len(caveats_value) > 20:
            raise ValueError("caveats must be a list with at most 20 entries")

        experiences = tuple(
            _bounded_text(item, "experience_highlight", 1000) for item in experiences_value
        )
        learning = tuple(
            _bounded_text(item, "learning_suggestion", 1000) for item in learning_value
        )
        suggestions = tuple(
            ImprovementSuggestion(
                priority=_bounded_text(item.get("priority", "medium"), "suggestion.priority", 20),
                issue=_bounded_text(item.get("issue"), "suggestion.issue", 500),
                recommendation=_bounded_text(
                    item.get("recommendation"), "suggestion.recommendation", 1000
                ),
                evidence=_normalize_empty_evidence(
                    _bounded_text(item.get("evidence", ""), "suggestion.evidence", 500)
                ),
            )
            for item in _dict_items(suggestions_value, "resume_improvements")
        )
        caveats = tuple(_bounded_text(item, "caveat", 500) for item in caveats_value)
        return cls(
            summary=summary,
            technical_skills=technical_skills,
            soft_skills=soft_skills,
            experience_assessment=experience_assessment,
            experience_highlights=experiences,
            learning_suggestions=learning,
            resume_improvements=suggestions,
            caveats=caveats,
        )


def _parse_skills(value: Any, field: str) -> tuple[Skill, ...]:
    if not isinstance(value, list) or len(value) > 50:
        raise ValueError(f"{field} must be a list with at most 50 entries")
    return tuple(
        Skill(
            name=_bounded_text(item.get("name"), f"{field}.name", 120),
            evidence=_bounded_text(item.get("evidence"), f"{field}.evidence", 500),
            inferred=_boolean(item.get("inferred", False), f"{field}.inferred"),
        )
        for item in _dict_items(value, field)
    )


def _dict_items(value: list[Any], field: str) -> list[dict[str, Any]]:
    if any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{field} entries must be objects")
    return value


def _bounded_text(value: Any, field: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text")
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise ValueError(f"{field} exceeds the {max_length}-character limit")
    if field != "suggestion.evidence" and not cleaned:
        raise ValueError(f"{field} must not be empty")
    return cleaned


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value


def _normalize_empty_evidence(value: str) -> str:
    if value.casefold().strip() in {"empty string", "none", "n/a", "not applicable"}:
        return ""
    return value
