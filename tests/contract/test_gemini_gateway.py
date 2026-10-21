"""Contract tests for the Gemini adapter using synthetic model responses."""

import json
from types import SimpleNamespace

import pytest

from app.config.settings import Settings
from integrations import gemini_gateway
from integrations.gemini_gateway import GeminiAnalysisGateway
from utils.errors import (
    InvalidModelResponseError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)


def valid_payload() -> dict[str, object]:
    return {
        "summary": "Synthetic early-career candidate.",
        "technical_skills": [
            {
                "name": "Python",
                "evidence": "Built a Python project",
                "inferred": False,
            }
        ],
        "soft_skills": [],
        "experience_assessment": "Project work is relevant early-career evidence.",
        "experience_highlights": ["Built a Python project"],
        "learning_suggestions": ["Practice SQL."],
        "resume_improvements": [],
        "caveats": [],
    }


def test_gemini_gateway_validates_structured_response(monkeypatch):
    captured: dict[str, object] = {}

    class FakeModels:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(text=json.dumps(valid_payload()))

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_options"] = kwargs
            self.models = FakeModels()

    monkeypatch.setattr(gemini_gateway.genai, "Client", FakeClient)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    settings = Settings.from_environment()

    result = GeminiAnalysisGateway(settings).analyze("Built a Python project")

    assert result.technical_skills[0].name == "Python"
    assert captured["model"] == settings.gemini_model
    config = captured["config"]
    assert config.response_mime_type == "application/json"
    assert captured["contents"] == json.dumps(
        {"resume_text": "Built a Python project"}, ensure_ascii=False
    )


def test_gemini_gateway_rejects_invalid_json(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            return SimpleNamespace(text="not-json")

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(gemini_gateway.genai, "Client", FakeClient)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")

    with pytest.raises(InvalidModelResponseError):
        GeminiAnalysisGateway(Settings.from_environment()).analyze("Synthetic resume text")


def test_gemini_gateway_maps_authentication_error(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            raise gemini_gateway.errors.ClientError(
                403,
                {"error": {"message": "synthetic authorization failure"}},
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(gemini_gateway.genai, "Client", FakeClient)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")

    with pytest.raises(ProviderConfigurationError):
        GeminiAnalysisGateway(Settings.from_environment()).analyze("Synthetic resume text")


def test_gemini_gateway_maps_invalid_key_400(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            raise gemini_gateway.errors.ClientError(
                400,
                {"error": {"message": "API key not valid. Please pass a valid API key."}},
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(gemini_gateway.genai, "Client", FakeClient)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")

    with pytest.raises(ProviderConfigurationError):
        GeminiAnalysisGateway(Settings.from_environment()).analyze("Synthetic resume text")


def test_gemini_gateway_retries_temporary_server_errors(monkeypatch):
    calls = 0

    class FakeModels:
        def generate_content(self, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise gemini_gateway.errors.ServerError(
                    503,
                    {"error": {"message": "synthetic temporary outage"}},
                )
            return SimpleNamespace(text=json.dumps(valid_payload()))

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(gemini_gateway.genai, "Client", FakeClient)
    monkeypatch.setattr(gemini_gateway.time, "sleep", lambda _: None)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "1")

    result = GeminiAnalysisGateway(Settings.from_environment()).analyze("Synthetic resume text")

    assert result.summary == "Synthetic early-career candidate."
    assert calls == 2


def test_gemini_gateway_reports_server_outage_after_retry_exhaustion(monkeypatch):
    calls = 0

    class FakeModels:
        def generate_content(self, **kwargs):
            nonlocal calls
            calls += 1
            raise gemini_gateway.errors.ServerError(
                503,
                {"error": {"message": "synthetic temporary outage"}},
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(gemini_gateway.genai, "Client", FakeClient)
    monkeypatch.setattr(gemini_gateway.time, "sleep", lambda _: None)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "1")

    with pytest.raises(ProviderUnavailableError):
        GeminiAnalysisGateway(Settings.from_environment()).analyze("Synthetic resume text")
    assert calls == 2


def test_gemini_gateway_maps_rate_limit_to_quota_message(monkeypatch):
    class FakeModels:
        def generate_content(self, **kwargs):
            raise gemini_gateway.errors.ClientError(
                429,
                {"error": {"message": "synthetic quota exceeded"}},
            )

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(gemini_gateway.genai, "Client", FakeClient)
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-key")

    with pytest.raises(ProviderRateLimitError) as error:
        GeminiAnalysisGateway(Settings.from_environment()).analyze("Synthetic resume text")
    assert "free-tier quota" in error.value.user_message
