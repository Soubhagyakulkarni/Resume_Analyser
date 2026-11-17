"""Integration tests for the SQLite job catalog."""


def test_repository_initializes_and_reads_jobs(tmp_path, sample_job):
    from repositories.sqlite_job_repository import SQLiteJobRepository

    repository = SQLiteJobRepository(tmp_path / "jobs.sqlite3")
    repository.replace_jobs([sample_job])

    assert repository.list_active_jobs() == [sample_job]


def test_catalog_refresh_replaces_existing_records(tmp_path, sample_job):
    from dataclasses import replace

    from repositories.sqlite_job_repository import SQLiteJobRepository

    repository = SQLiteJobRepository(tmp_path / "jobs.sqlite3")
    repository.replace_jobs([sample_job])
    replacement = replace(sample_job, id="job-2", title="Junior Developer")
    repository.replace_jobs([replacement])

    assert repository.list_active_jobs() == [replacement]
