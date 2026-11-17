from types import SimpleNamespace

import pytest

from app.utils.errors import CatalogUnavailableError
from repositories.supabase_job_repository import SupabaseJobRepository


class FakeQuery:
    def __init__(self, data):
        self.data = data

    def select(self, _fields):
        return self

    def eq(self, _field, _value):
        return self

    def order(self, _field, desc=False):
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


def test_supabase_job_repository_maps_postgres_records(sample_job):
    row = {
        "id": sample_job.id,
        "title": sample_job.title,
        "description": sample_job.description,
        "required_skills": list(sample_job.required_skills),
        "location": sample_job.location,
        "application_url": sample_job.application_url,
        "source": sample_job.source,
        "updated_at": sample_job.updated_at.isoformat(),
    }

    class FakeClient:
        def table(self, name):
            assert name == "jobs"
            return FakeQuery([row])

    assert SupabaseJobRepository(FakeClient()).list_active_jobs() == [sample_job]


def test_supabase_job_repository_rejects_invalid_skills():
    class FakeClient:
        def table(self, _name):
            return FakeQuery(
                [
                    {
                        "id": "job-1",
                        "title": "Engineer",
                        "description": "",
                        "required_skills": "Python",
                        "location": "",
                        "application_url": "",
                        "source": "fixture",
                        "updated_at": "2026-11-16",
                    }
                ]
            )

    with pytest.raises(CatalogUnavailableError):
        SupabaseJobRepository(FakeClient()).list_active_jobs()


def test_supabase_job_repository_refuses_empty_catalog_replacement():
    class FakeClient:
        def rpc(self, *_args, **_kwargs):
            raise AssertionError("an empty replacement must not reach the database")

    with pytest.raises(ValueError, match="empty list"):
        SupabaseJobRepository(FakeClient()).replace_jobs([])
