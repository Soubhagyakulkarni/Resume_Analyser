import json
import sqlite3
from datetime import UTC, datetime

import pytest

from scripts.migrate_sqlite_jobs_to_supabase import migrate_legacy_catalog


def _create_legacy_catalog(path):
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                required_skills_json TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                application_url TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO jobs (
                id, title, description, required_skills_json, location,
                application_url, source, updated_at, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "active",
                    "Python Engineer",
                    "Build software",
                    json.dumps(["Python", "SQL"]),
                    "Remote",
                    "https://jobs.example.com/active",
                    "Test source",
                    datetime.now(UTC).date().isoformat(),
                    1,
                ),
                (
                    "inactive",
                    "Old job",
                    "",
                    json.dumps(["Python"]),
                    "Remote",
                    "https://jobs.example.com/inactive",
                    "Test source",
                    datetime.now(UTC).date().isoformat(),
                    0,
                ),
            ],
        )


def test_migration_imports_active_rows_and_keeps_source_unchanged(tmp_path):
    source = tmp_path / "jobs.sqlite3"
    _create_legacy_catalog(source)

    class FakeRepository:
        jobs = None

        def replace_jobs(self, jobs):
            self.jobs = jobs

    repository = FakeRepository()
    count = migrate_legacy_catalog(source, repository)

    assert count == 1
    assert repository.jobs[0].id == "active"
    assert repository.jobs[0].required_skills == ("Python", "SQL")
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 2


def test_migration_refuses_empty_catalog_without_replacing(tmp_path):
    source = tmp_path / "jobs.sqlite3"
    _create_legacy_catalog(source)
    with sqlite3.connect(source) as connection:
        connection.execute("UPDATE jobs SET active = 0")

    class FakeRepository:
        def replace_jobs(self, _jobs):
            raise AssertionError("an empty catalog must not replace the target")

    with pytest.raises(ValueError, match="no active listings"):
        migrate_legacy_catalog(source, FakeRepository())
