"""Tests for deterministic job matching and gap wording."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from models.job import Job
from scripts.refresh_job_catalog import load_jobs
from utils.url_validation import is_placeholder_application_url


class FakeRepository:
    def __init__(self, jobs):
        self.jobs = jobs

    def list_active_jobs(self):
        return self.jobs


def test_recommends_matching_jobs_and_labels_unmentioned_skills(sample_analysis, sample_job):
    from services.recommendation_service import RecommendationService

    recommendations = RecommendationService(FakeRepository([sample_job])).recommend(sample_analysis)
    assert len(recommendations) == 1
    assert recommendations[0].matched_skills == ("Python",)
    assert recommendations[0].missing_from_resume == ("SQL",)
    assert "not found in this resume" in recommendations[0].rationale


def test_does_not_recommend_jobs_with_no_skill_overlap(sample_analysis, sample_job):
    from dataclasses import replace

    from services.recommendation_service import RecommendationService

    unrelated = replace(sample_job, required_skills=("Kubernetes",))
    assert RecommendationService(FakeRepository([unrelated])).recommend(sample_analysis) == []


def test_recommendations_exclude_stale_and_future_listings(sample_analysis, sample_job):
    from dataclasses import replace

    from services.recommendation_service import RecommendationService

    today = datetime.now(UTC).date()
    fresh = replace(sample_job, updated_at=today)
    stale = replace(sample_job, id="stale", updated_at=today - timedelta(days=31))
    future = replace(sample_job, id="future", updated_at=today + timedelta(days=1))
    service = RecommendationService(FakeRepository([fresh, stale, future]), max_age_days=30)

    assert [item.job.id for item in service.recommend(sample_analysis)] == ["job-1"]
    assert service.catalog_status().total_count == 3
    assert service.catalog_status().current_count == 1
    assert service.catalog_status().stale_count == 1
    assert service.catalog_status().future_dated_count == 1


def test_recommendations_include_listing_at_freshness_boundary(sample_analysis, sample_job):
    from dataclasses import replace

    from services.recommendation_service import RecommendationService

    boundary_job = replace(sample_job, updated_at=datetime.now(UTC).date() - timedelta(days=30))
    service = RecommendationService(FakeRepository([boundary_job]), max_age_days=30)

    assert len(service.recommend(sample_analysis)) == 1


def test_current_jobs_can_be_browsed_without_resume_skill_match(sample_analysis, sample_job):
    from dataclasses import replace

    from services.recommendation_service import RecommendationService

    role_without_extracted_skills = replace(
        sample_job,
        required_skills=(),
        title="Graduate Engineer Trainee",
    )
    service = RecommendationService(FakeRepository([role_without_extracted_skills]))

    assert service.recommend(sample_analysis) == []
    assert service.current_jobs() == [role_without_extracted_skills]


def test_current_jobs_are_limited_and_ordered_by_recency(sample_job):
    from dataclasses import replace

    from services.recommendation_service import RecommendationService

    today = datetime.now(UTC).date()
    jobs = [
        replace(sample_job, id=f"job-{days_ago}", updated_at=today - timedelta(days=days_ago))
        for days_ago in (2, 1, 3)
    ]
    service = RecommendationService(FakeRepository(jobs))

    assert [job.id for job in service.current_jobs(limit=2)] == ["job-1", "job-2"]


def test_current_jobs_reject_nonpositive_limit(sample_job):
    from services.recommendation_service import RecommendationService

    with pytest.raises(ValueError, match="limit must be positive"):
        RecommendationService(FakeRepository([sample_job])).current_jobs(limit=0)


def test_role_and_location_preferences_filter_recommendations_and_browse_jobs(sample_analysis):
    from datetime import UTC, datetime

    from models.job import Job
    from services.recommendation_service import JobSearchPreferences, RecommendationService

    posted = datetime.now(UTC).date()
    jobs = [
        Job(
            id="software-bengaluru",
            title="Graduate Software Engineer",
            description="Build software",
            required_skills=("Python", "SQL"),
            location="Bengaluru, India",
            application_url="https://careers.example.com/software",
            source="Fixture",
            updated_at=posted,
        ),
        Job(
            id="software-hyderabad",
            title="Graduate Software Engineer",
            description="Build software",
            required_skills=("Python",),
            location="Hyderabad, India",
            application_url="https://careers.example.com/hyderabad",
            source="Fixture",
            updated_at=posted,
        ),
        Job(
            id="analyst-bengaluru",
            title="Graduate Data Analyst",
            description="Analyze data",
            required_skills=("Python",),
            location="Bengaluru, India",
            application_url="https://careers.example.com/analyst",
            source="Fixture",
            updated_at=posted,
        ),
    ]
    preferences = JobSearchPreferences(
        role_keywords=("software engineer", "developer"),
        location="BENGALURU",
    )
    service = RecommendationService(FakeRepository(jobs))

    recommendations = service.recommend(sample_analysis, preferences=preferences)
    status = service.catalog_status(preferences)
    browse_jobs = service.current_jobs(preferences=preferences)

    assert [item.job.id for item in recommendations] == ["software-bengaluru"]
    assert [job.id for job in browse_jobs] == ["software-bengaluru"]
    assert status.current_count == 3
    assert status.preference_match_count == 1
    assert preferences.has_filters is True


def test_preferences_allow_all_roles_and_locations_when_blank(sample_job):
    from services.recommendation_service import JobSearchPreferences, RecommendationService

    service = RecommendationService(FakeRepository([sample_job]))
    preferences = JobSearchPreferences()

    assert preferences.has_filters is False
    assert service.current_jobs(preferences=preferences) == [sample_job]


def test_preference_role_terms_are_or_matched_and_location_is_required(sample_analysis):
    from datetime import UTC, datetime

    from models.job import Job
    from services.recommendation_service import JobSearchPreferences, RecommendationService

    jobs = [
        Job(
            id=role,
            title=role,
            description="",
            required_skills=("Python",),
            location=location,
            application_url="",
            source="Fixture",
            updated_at=datetime.now(UTC).date(),
        )
        for role, location in (
            ("Graduate Software Engineer", "Bengaluru"),
            ("Graduate Data Analyst", "Bengaluru"),
            ("Graduate Data Analyst", "Chennai"),
        )
    ]
    preferences = JobSearchPreferences(
        role_keywords=("Software Engineer", "Data Analyst"),
        location="Bengaluru",
    )

    assert (
        len(
            RecommendationService(FakeRepository(jobs)).recommend(
                sample_analysis, preferences=preferences
            )
        )
        == 2
    )


@pytest.mark.parametrize("max_age_days", [0, 366])
def test_recommendation_service_rejects_invalid_freshness_window(max_age_days):
    from services.recommendation_service import RecommendationService

    with pytest.raises(ValueError, match="max_age_days"):
        RecommendationService(FakeRepository([]), max_age_days=max_age_days)


def test_job_model_rejects_non_https_application_urls():
    with pytest.raises(ValueError):
        Job(
            id="job-unsafe",
            title="Example role",
            description="",
            required_skills=("Python",),
            location="",
            application_url="http://jobs.example/apply",
            source="Fixture",
            updated_at=date(2026, 1, 1),
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://careers.example-tech.com/jobs/JOB003",
        "https://example.com/jobs/1",
        "https://jobs.example.test/opening",
        "https://employer.invalid/role",
    ],
)
def test_placeholder_application_domains_are_rejected(url):
    assert is_placeholder_application_url(url)


def test_real_looking_application_domain_is_not_rejected_as_placeholder():
    assert not is_placeholder_application_url("https://careers.acme.com/jobs/123")


def test_sample_catalog_cannot_be_imported_as_real_jobs():
    fixture = Path(__file__).parents[1] / "fixtures" / "sample_jobs.csv"

    with pytest.raises(ValueError, match="placeholder application domain"):
        load_jobs(fixture)
