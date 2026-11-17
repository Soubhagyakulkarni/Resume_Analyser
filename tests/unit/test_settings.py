"""Tests for runtime configuration validation."""

import pytest

from app.config.settings import Settings


def test_settings_load_api_key_and_limits_from_environment(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("OPENAI_API_KEY", " test-secret ")
    monkeypatch.setenv("GEMINI_API_KEY", " gemini-secret ")
    monkeypatch.setenv("MAX_RESUME_CHARS", "1000")
    monkeypatch.setenv("JOB_LISTING_MAX_AGE_DAYS", "45")
    monkeypatch.setenv("ADZUNA_APP_ID", "synthetic-app-id")
    monkeypatch.setenv("ADZUNA_APP_KEY", "synthetic-app-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-flash-latest")
    monkeypatch.setenv("SUPABASE_URL", " https://example.supabase.co/ ")
    monkeypatch.setenv("SUPABASE_ANON_KEY", " anon-key ")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", " service-role-key ")

    settings = Settings.from_environment()

    assert settings.openai_api_key == "test-secret"
    assert settings.ai_provider == "gemini"
    assert settings.gemini_api_key == "gemini-secret"
    assert settings.gemini_model == "gemini-flash-latest"
    assert settings.max_resume_chars == 1000
    assert settings.job_listing_max_age_days == 45
    assert settings.adzuna_app_id == "synthetic-app-id"
    assert settings.adzuna_app_key == "synthetic-app-key"
    assert settings.adzuna_country_code == "in"
    assert settings.supabase_url == "https://example.supabase.co"
    assert settings.supabase_anon_key == "anon-key"
    assert settings.supabase_service_role_key == "service-role-key"


def test_settings_reject_insecure_supabase_url(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://example.com")

    with pytest.raises(ValueError, match="SUPABASE_URL must use HTTPS"):
        Settings.from_environment()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MAX_UPLOAD_BYTES", "0"),
        ("MAX_RESUME_CHARS", "not-an-integer"),
        ("OPENAI_TIMEOUT_SECONDS", "nan"),
        ("OPENAI_MODEL", " "),
        ("AI_PROVIDER", "unknown"),
        ("JOB_LISTING_MAX_AGE_DAYS", "0"),
        ("JOB_LISTING_MAX_AGE_DAYS", "366"),
        ("ADZUNA_COUNTRY_CODE", "India"),
    ],
)
def test_settings_reject_invalid_runtime_values(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        Settings.from_environment()


def test_settings_defaults_to_openai(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    settings = Settings.from_environment()
    assert settings.ai_provider == "openai"
