"""SQLite-backed repository for authorized job catalog records."""

import json
import logging
import sqlite3
from datetime import date
from pathlib import Path

from app.utils.errors import CatalogUnavailableError
from models.job import Job

logger = logging.getLogger(__name__)
MIGRATION = Path(__file__).with_name("migrations") / "001_create_job_catalog.sql"


class SQLiteJobRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as connection:
                connection.executescript(MIGRATION.read_text(encoding="utf-8"))
        except (OSError, sqlite3.Error) as exc:
            logger.exception("Could not initialize SQLite job catalog")
            raise CatalogUnavailableError() from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def list_active_jobs(self) -> list[Job]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT id, title, description, required_skills_json, location,
                           application_url, source, updated_at
                    FROM jobs
                    WHERE active = 1
                    ORDER BY updated_at DESC, title COLLATE NOCASE
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            logger.exception("Could not read active job catalog")
            raise CatalogUnavailableError() from exc

        try:
            return [
                Job(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    required_skills=tuple(json.loads(row["required_skills_json"])),
                    location=row["location"],
                    application_url=row["application_url"],
                    source=row["source"],
                    updated_at=date.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.exception("Job catalog contains an invalid record")
            raise CatalogUnavailableError() from exc

    def replace_jobs(self, jobs: list[Job]) -> None:
        """Replace catalog data atomically; intended for the authorized import command."""
        try:
            with self._connect() as connection:
                connection.execute("DELETE FROM jobs")
                connection.executemany(
                    """
                    INSERT INTO jobs (
                        id, title, description, required_skills_json, location,
                        application_url, source, updated_at, active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    [
                        (
                            job.id,
                            job.title,
                            job.description,
                            json.dumps(job.required_skills),
                            job.location,
                            job.application_url,
                            job.source,
                            job.updated_at.isoformat(),
                        )
                        for job in jobs
                    ],
                )
        except (sqlite3.Error, TypeError, ValueError) as exc:
            logger.exception("Could not refresh job catalog")
            raise CatalogUnavailableError() from exc
