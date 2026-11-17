"""One-time, read-only import of a legacy SQLite job catalog into Supabase."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

from supabase import create_client

from app.config.settings import PROJECT_ROOT, Settings
from app.utils.errors import ApplicationError
from models.job import Job
from repositories.supabase_job_repository import SupabaseJobRepository


def load_legacy_jobs(database_path: Path) -> list[Job]:
    """Read active legacy jobs without modifying the source database."""
    database_path = database_path.expanduser().resolve()
    if not database_path.is_file():
        raise FileNotFoundError(f"Legacy SQLite catalog not found: {database_path}")
    uri = f"file:{database_path.as_posix()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as connection:
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
        raise ValueError("Could not read the legacy jobs table.") from exc

    try:
        return [
            Job(
                id=row[0],
                title=row[1],
                description=row[2] or "",
                required_skills=tuple(json.loads(row[3])),
                location=row[4] or "",
                application_url=row[5] or "",
                source=row[6],
                updated_at=date.fromisoformat(row[7]),
            )
            for row in rows
        ]
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("The legacy job catalog contains an invalid record.") from exc


def migrate_legacy_catalog(database_path: Path, repository: SupabaseJobRepository) -> int:
    jobs = load_legacy_jobs(database_path)
    if not jobs:
        raise ValueError("The legacy job catalog has no active listings; nothing was changed.")
    repository.replace_jobs(jobs)
    return len(jobs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "database",
        nargs="?",
        type=Path,
        default=PROJECT_ROOT / "data" / "jobs.sqlite3",
        help="Legacy SQLite database path (default: data/jobs.sqlite3)",
    )
    args = parser.parse_args()

    try:
        settings = Settings.from_environment()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env first.")
        repository = SupabaseJobRepository(
            create_client(settings.supabase_url, settings.supabase_service_role_key)
        )
        count = migrate_legacy_catalog(args.database, repository)
    except ApplicationError as exc:
        print(f"Job catalog migration failed: {exc.user_message}")
        return 1
    except (OSError, ValueError) as exc:
        print(f"Job catalog migration failed: {exc}")
        return 1

    print(f"Imported {count} active job listings into Supabase PostgreSQL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
