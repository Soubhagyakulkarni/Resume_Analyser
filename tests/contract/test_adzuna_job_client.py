"""Contract tests for the Adzuna adapter using synthetic API responses."""

import json
from datetime import UTC, datetime, timedelta
from io import BytesIO
from urllib.error import HTTPError

import pytest

from app.utils.errors import JobSourceUnavailableError
from integrations import adzuna_job_client
from integrations.adzuna_job_client import AdzunaJobClient


def listing(**overrides):
    record = {
        "id": "synthetic-123",
        "title": "Junior **Python** Developer",
        "description": (
            "<p>Build Python services and perform Data Analysis with SQL.</p>"
            "<p>Use <strong>Git</strong> for version control.</p>"
        ),
        "created": (datetime.now(UTC).date() - timedelta(days=2)).isoformat(),
        "redirect_url": "https://jobs.acme.example.invalid/apply",
        "location": {"display_name": "Bengaluru, India"},
        "company": {"display_name": "Synthetic Company"},
    }
    record.update(overrides)
    return record


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, size=-1):
        return self.payload[:size]


def test_adzuna_client_maps_api_jobs_and_limits_credentials_to_request(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return FakeResponse({"results": [listing()]})

    monkeypatch.setattr(adzuna_job_client, "urlopen", fake_urlopen)
    client = AdzunaJobClient("synthetic-app-id", "synthetic-app-key", country_code="in")

    jobs = client.search(what="Python developer", where="Bengaluru", pages=1)

    assert len(jobs) == 1
    job = jobs[0]
    assert job.id == "adzuna-in-synthetic-123"
    assert job.title == "Junior Python Developer"
    assert job.required_skills == ("Data Analysis", "Python", "SQL", "Git")
    assert job.location == "Bengaluru, India"
    assert job.application_url == ""
    assert job.source == "Adzuna"
    assert "app_id=synthetic-app-id" in captured["url"]
    assert "app_key=synthetic-app-key" in captured["url"]
    assert captured["timeout"] == 20


def test_adzuna_client_preserves_valid_https_apply_url(monkeypatch):
    monkeypatch.setattr(
        adzuna_job_client,
        "urlopen",
        lambda request, timeout: FakeResponse(
            {"results": [listing(redirect_url="https://jobs.acme.com/apply/123")]}
        ),
    )
    client = AdzunaJobClient("id", "key")

    jobs = client.search("Python", "India", pages=1)

    assert jobs[0].application_url == "https://jobs.acme.com/apply/123"


def test_adzuna_client_adds_india_country_to_city_state_location(monkeypatch):
    monkeypatch.setattr(
        adzuna_job_client,
        "urlopen",
        lambda request, timeout: FakeResponse(
            {"results": [listing(location={"display_name": "Bengaluru, Karnataka"})]}
        ),
    )
    client = AdzunaJobClient("id", "key", country_code="in")

    jobs = client.search("Python", "India", pages=1)

    assert jobs[0].location == "Bengaluru, Karnataka, India"


def test_adzuna_client_rejects_provider_errors_without_exposing_credentials(monkeypatch):
    secret = "synthetic-secret-key"

    def raise_http_error(request, timeout):
        raise HTTPError(request.full_url, 403, "forbidden", None, BytesIO(b""))

    monkeypatch.setattr(adzuna_job_client, "urlopen", raise_http_error)
    client = AdzunaJobClient("id", secret)

    with pytest.raises(JobSourceUnavailableError) as error:
        client.search("Python", "India", pages=1)

    assert secret not in str(error.value)


def test_adzuna_client_rejects_malformed_response(monkeypatch):
    monkeypatch.setattr(
        adzuna_job_client,
        "urlopen",
        lambda request, timeout: FakeResponse({"unexpected": []}),
    )
    client = AdzunaJobClient("id", "key")

    with pytest.raises(JobSourceUnavailableError):
        client.search("Python", "India", pages=1)


def test_adzuna_client_skips_malformed_job_records(monkeypatch):
    monkeypatch.setattr(
        adzuna_job_client,
        "urlopen",
        lambda request, timeout: FakeResponse({"results": [{"title": "Missing ID"}, listing()]}),
    )
    client = AdzunaJobClient("id", "key")

    jobs = client.search("Python", "India", pages=1)

    assert len(jobs) == 1
    assert jobs[0].id == "adzuna-in-synthetic-123"
