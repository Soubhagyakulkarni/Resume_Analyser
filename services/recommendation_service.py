"""Deterministic job matching and missing-from-resume analysis."""

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from models.analysis import ResumeAnalysis
from models.job import Job, JobRecommendation
from services.ports import JobRepository


@dataclass(frozen=True, slots=True)
class JobCatalogStatus:
    total_count: int
    current_count: int
    preference_match_count: int
    stale_count: int
    future_dated_count: int
    max_age_days: int
    latest_updated_at: date | None


@dataclass(frozen=True, slots=True)
class JobSearchPreferences:
    """Optional, session-only filters for role titles and job locations."""

    role_keywords: tuple[str, ...] = ()
    location: str = ""

    @property
    def has_filters(self) -> bool:
        return bool(
            any(_normalize(term) for term in self.role_keywords) or _normalize(self.location)
        )


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]+", " ", value.casefold()).strip()


class RecommendationService:
    def __init__(self, repository: JobRepository, max_age_days: int = 30) -> None:
        if not 1 <= max_age_days <= 365:
            raise ValueError("max_age_days must be between 1 and 365")
        self._repository = repository
        self._max_age_days = max_age_days

    def recommend(
        self,
        analysis: ResumeAnalysis,
        limit: int = 10,
        preferences: JobSearchPreferences | None = None,
    ) -> list[JobRecommendation]:
        if limit < 1:
            raise ValueError("limit must be positive")
        resume_skills = {_normalize(skill.name) for skill in analysis.skills}
        recommendations: list[JobRecommendation] = []
        today = datetime.now(UTC).date()
        for job in self._filter_preferences(self._current_jobs(today), preferences):
            requirements_by_key = {
                _normalize(skill): skill for skill in job.required_skills if _normalize(skill)
            }
            if not requirements_by_key:
                continue
            matched = tuple(
                skill
                for normalized, skill in requirements_by_key.items()
                if normalized in resume_skills
            )
            missing = tuple(
                skill
                for normalized, skill in requirements_by_key.items()
                if normalized not in resume_skills
            )
            if not matched:
                continue
            ratio = len(matched) / len(requirements_by_key)
            recommendations.append(
                JobRecommendation(
                    job=job,
                    matched_skills=matched,
                    missing_from_resume=missing,
                    match_ratio=ratio,
                    rationale=(
                        f"{len(matched)} of {len(requirements_by_key)} listed skills are evidenced "
                        "in the resume analysis. Unmatched skills were not found in this resume."
                    ),
                )
            )
        recommendations.sort(key=lambda result: (-result.match_ratio, result.job.title.casefold()))
        return recommendations[:limit]

    def catalog_status(self, preferences: JobSearchPreferences | None = None) -> JobCatalogStatus:
        """Report active catalog coverage using the same freshness rule as matching."""
        jobs = self._repository.list_active_jobs()
        today = datetime.now(UTC).date()
        earliest_current_date = today - timedelta(days=self._max_age_days)
        current_jobs = [job for job in jobs if earliest_current_date <= job.updated_at <= today]
        current_count = len(current_jobs)
        preference_match_count = len(self._filter_preferences(current_jobs, preferences))
        stale_count = sum(job.updated_at < earliest_current_date for job in jobs)
        future_dated_count = sum(job.updated_at > today for job in jobs)
        return JobCatalogStatus(
            total_count=len(jobs),
            current_count=current_count,
            preference_match_count=preference_match_count,
            stale_count=stale_count,
            future_dated_count=future_dated_count,
            max_age_days=self._max_age_days,
            latest_updated_at=max((job.updated_at for job in jobs), default=None),
        )

    def current_jobs(
        self,
        limit: int = 10,
        preferences: JobSearchPreferences | None = None,
    ) -> list[Job]:
        """Return fresh catalog listings for explicit browsing, not resume matching."""
        if limit < 1:
            raise ValueError("limit must be positive")
        jobs = self._filter_preferences(
            self._current_jobs(datetime.now(UTC).date()),
            preferences,
        )
        jobs.sort(key=lambda job: (-job.updated_at.toordinal(), job.title.casefold()))
        return jobs[:limit]

    @staticmethod
    def _filter_preferences(
        jobs: list[Job],
        preferences: JobSearchPreferences | None,
    ) -> list[Job]:
        if preferences is None or not preferences.has_filters:
            return jobs

        role_terms = tuple(
            _normalize(term) for term in preferences.role_keywords if _normalize(term)
        )
        location_term = _normalize(preferences.location)
        filtered = []
        for job in jobs:
            title = _normalize(job.title)
            location = _normalize(job.location)
            if role_terms and not any(term in title for term in role_terms):
                continue
            if location_term and location_term not in location:
                continue
            filtered.append(job)
        return filtered

    def _current_jobs(self, today: date) -> list[Job]:
        earliest_current_date = today - timedelta(days=self._max_age_days)
        return [
            job
            for job in self._repository.list_active_jobs()
            if earliest_current_date <= job.updated_at <= today
        ]
