"""Automatic seeder and sync service for the SQLite job catalog."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config.settings import Settings
from integrations.adzuna_job_client import AdzunaJobClient
from models.job import Job
from repositories.sqlite_job_repository import SQLiteJobRepository

logger = logging.getLogger(__name__)
SEED_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "seed_catalog.json"


def ensure_job_catalog(
    repository: SQLiteJobRepository,
    settings: Settings,
    force_refresh: bool = False,
    search_query: str | None = None,
    location_query: str | None = None,
) -> int:
    """Ensure the catalog contains active, non-stale job listings with skills."""
    today = datetime.now(UTC).date()
    earliest_date = today - timedelta(days=settings.job_listing_max_age_days)

    if not hasattr(repository, "replace_jobs"):
        return 0

    if not force_refresh:
        try:
            active_jobs = repository.list_active_jobs()
            fresh_with_skills = [
                job
                for job in active_jobs
                if earliest_date <= job.updated_at <= today and bool(job.required_skills)
            ]
            if len(fresh_with_skills) >= 10:
                return len(fresh_with_skills)
        except Exception as exc:
            logger.warning("Could not inspect existing job catalog: %s", exc)

    adzuna_jobs: list[Job] = []
    if settings.adzuna_app_id and settings.adzuna_app_key:
        try:
            client = AdzunaJobClient(
                settings.adzuna_app_id,
                settings.adzuna_app_key,
                country_code=settings.adzuna_country_code,
            )
            what_term = search_query or "developer"
            where_term = location_query or "India"
            batch = client.search(what=what_term, where=where_term, pages=2)
            if batch:
                adzuna_jobs.extend(batch)
                logger.info("Retrieved %d live listings from Adzuna", len(batch))
        except Exception as exc:
            logger.warning("Adzuna fetch failed; falling back to seed catalog: %s", exc)

    seed_jobs: list[Job] = []
    if SEED_CATALOG_PATH.is_file():
        try:
            with SEED_CATALOG_PATH.open(encoding="utf-8") as file:
                items = json.load(file)
            for item in items:
                seed_jobs.append(
                    Job(
                        id=str(item["id"]),
                        title=str(item["title"]),
                        description=str(item.get("description", "")),
                        required_skills=tuple(item.get("required_skills", ())),
                        location=str(item.get("location", "India")),
                        application_url=str(
                            item.get("application_url", "https://www.adzuna.in/details/seed")
                        ),
                        source=str(item.get("source", "Market Feed")),
                        updated_at=today,
                    )
                )
        except Exception as exc:
            logger.warning("Failed to load seed catalog JSON: %s", exc)

    seen_ids: set[str] = set()
    combined: list[Job] = []
    for job in adzuna_jobs + seed_jobs:
        if job.id not in seen_ids:
            seen_ids.add(job.id)
            combined.append(job)

    if combined:
        repository.replace_jobs(combined)
        logger.info("Job catalog successfully refreshed with %d jobs", len(combined))
        return len(combined)

    return 0
