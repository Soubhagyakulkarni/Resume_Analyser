"""Tests for safe Adzuna catalog refresh behavior."""

from datetime import UTC, datetime

import pytest

from models.job import Job
from scripts.refresh_adzuna_catalog import refresh_catalog


class FakeClient:
    def __init__(self, jobs):
        self.jobs = jobs

    def search(self, what, where, pages):
        return self.jobs


class FakeCatalog:
    def __init__(self):
        self.replacements = []

    def replace_jobs(self, jobs):
        self.replacements.append(jobs)


def test_refresh_replaces_catalog_only_after_nonempty_success():
    job = Job(
        id="adzuna-in-1",
        title="Synthetic Software Developer",
        description="",
        required_skills=("Python",),
        location="India",
        application_url="",
        source="Adzuna",
        updated_at=datetime.now(UTC).date(),
    )
    catalog = FakeCatalog()

    imported = refresh_catalog(
        FakeClient([job]),
        catalog,
        what="software developer",
        where="India",
        pages=1,
    )

    assert imported == 1
    assert catalog.replacements == [[job]]


def test_empty_refresh_does_not_replace_existing_catalog():
    catalog = FakeCatalog()

    with pytest.raises(ValueError, match="existing job catalog was left unchanged"):
        refresh_catalog(
            FakeClient([]),
            catalog,
            what="software developer",
            where="India",
            pages=1,
        )

    assert catalog.replacements == []
