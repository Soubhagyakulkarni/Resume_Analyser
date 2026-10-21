"""Tests for deterministic ordering of current job recommendations."""

from dataclasses import replace
from datetime import timedelta

from models.job import JobRecommendation
from services.career_profile import sort_job_recommendations


def _recommendation(job, ratio):
    return JobRecommendation(
        job=job,
        matched_skills=("Python",),
        missing_from_resume=("SQL",),
        match_ratio=ratio,
        rationale="Synthetic match",
    )


def test_relevance_sort_orders_by_match_then_title(sample_job):
    lower_match = _recommendation(replace(sample_job, title="A Role"), 0.4)
    higher_match = _recommendation(replace(sample_job, title="Z Role"), 0.9)

    assert sort_job_recommendations([lower_match, higher_match]) == [
        higher_match,
        lower_match,
    ]


def test_newest_sort_uses_listing_date_then_match(sample_job):
    older = _recommendation(sample_job, 0.9)
    newer_job = replace(
        sample_job,
        id="newer",
        updated_at=sample_job.updated_at + timedelta(days=1),
    )
    newer = _recommendation(newer_job, 0.4)

    assert sort_job_recommendations([older, newer], "Newest") == [newer, older]


def test_location_sort_is_case_insensitive_and_does_not_mutate_input(sample_job):
    bengaluru = _recommendation(replace(sample_job, location="Bengaluru"), 0.4)
    hyderabad = _recommendation(replace(sample_job, location="hyderabad"), 0.9)
    original = [hyderabad, bengaluru]

    ordered = sort_job_recommendations(original, "Location")

    assert ordered == [bengaluru, hyderabad]
    assert original == [hyderabad, bengaluru]
