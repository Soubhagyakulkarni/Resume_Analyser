"""Unit tests for catalog seeder behavior."""

from datetime import UTC, datetime
from pathlib import Path

from app.config.settings import Settings
from models.job import Job
from services.catalog_seeder import ensure_job_catalog


class FakeRepository:
    def __init__(self, existing_jobs=None):
        self.jobs = list(existing_jobs or [])

    def list_active_jobs(self):
        return self.jobs

    def replace_jobs(self, jobs):
        self.jobs = list(jobs)


def test_catalog_seeder_populates_empty_repository(tmp_path):
    repo = FakeRepository()
    settings = Settings(
        ai_provider="openai",
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        gemini_api_key=None,
        gemini_model="gemini-3.5-flash",
        openai_timeout_seconds=45.0,
        openai_max_retries=3,
        max_upload_bytes=10 * 1024 * 1024,
        max_resume_chars=50000,
        sqlite_database_path=tmp_path / "jobs.sqlite3",
        job_listing_max_age_days=30,
        adzuna_app_id=None,
        adzuna_app_key=None,
        adzuna_country_code="in",
        log_level="INFO",
    )

    count = ensure_job_catalog(repo, settings)
    assert count >= 10
    assert len(repo.jobs) >= 10
    assert any("Python" in job.required_skills for job in repo.jobs)


def test_catalog_seeder_skips_when_already_fresh():
    today = datetime.now(UTC).date()
    existing = [
        Job(
            id=f"test-{i}",
            title=f"Engineer {i}",
            description="",
            required_skills=("Python", "SQL"),
            location="India",
            application_url="https://www.adzuna.in/details/test",
            source="Test",
            updated_at=today,
        )
        for i in range(12)
    ]
    repo = FakeRepository(existing)
    settings = Settings(
        ai_provider="openai",
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        gemini_api_key=None,
        gemini_model="gemini-3.5-flash",
        openai_timeout_seconds=45.0,
        openai_max_retries=3,
        max_upload_bytes=10 * 1024 * 1024,
        max_resume_chars=50000,
        sqlite_database_path=Path("jobs.sqlite3"),
        job_listing_max_age_days=30,
        adzuna_app_id=None,
        adzuna_app_key=None,
        adzuna_country_code="in",
        log_level="INFO",
    )

    count = ensure_job_catalog(repo, settings)
    assert count == 12
    # Ensure no overwrite occurred
    assert repo.jobs == existing
