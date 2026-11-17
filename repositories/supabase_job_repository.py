"""Supabase Postgres repository for the authorized job catalog."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from postgrest.exceptions import APIError
from supabase import Client

from app.utils.errors import CatalogUnavailableError
from models.job import Job

logger = logging.getLogger(__name__)


class SupabaseJobRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def list_active_jobs(self) -> list[Job]:
        try:
            response = (
                self._client.table("jobs")
                .select(
                    "id,title,description,required_skills,location,application_url,source,updated_at"
                )
                .eq("active", True)
                .order("updated_at", desc=True)
                .execute()
            )
            return [self._row_to_job(row) for row in response.data]
        except (KeyError, TypeError, ValueError) as exc:
            logger.exception("Supabase job catalog contains an invalid record")
            raise CatalogUnavailableError() from exc
        except (APIError, httpx.HTTPError) as exc:
            logger.exception("Could not read Supabase job catalog")
            raise CatalogUnavailableError() from exc

    def replace_jobs(self, jobs: list[Job]) -> None:
        """Replace catalog data atomically using the service-role-only SQL function."""
        if not jobs:
            raise ValueError("Refusing to replace the job catalog with an empty list")
        records = [
            {
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "required_skills": list(job.required_skills),
                "location": job.location,
                "application_url": job.application_url,
                "source": job.source,
                "updated_at": job.updated_at.isoformat(),
                "active": True,
            }
            for job in jobs
        ]
        try:
            self._client.rpc("replace_job_catalog", {"p_jobs": records}).execute()
        except (APIError, httpx.HTTPError, TypeError, ValueError) as exc:
            logger.exception("Could not refresh Supabase job catalog")
            raise CatalogUnavailableError() from exc

    @staticmethod
    def _row_to_job(row: dict[str, Any]) -> Job:
        skills = row["required_skills"]
        if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
            raise ValueError("required_skills must be an array of strings")
        return Job(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            required_skills=tuple(skills),
            location=row["location"] or "",
            application_url=row["application_url"] or "",
            source=row["source"],
            updated_at=date.fromisoformat(row["updated_at"]),
        )
