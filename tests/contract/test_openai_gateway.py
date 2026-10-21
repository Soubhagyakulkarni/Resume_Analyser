"""Contract tests for structured OpenAI response validation."""

import pytest

from models.analysis import ResumeAnalysis


def test_synthetic_model_response_matches_analysis_contract():
    payload = {
        "summary": "Early-career candidate with project experience.",
        "technical_skills": [
            {"name": "Python", "evidence": "Built a Python data project", "inferred": False}
        ],
        "soft_skills": [],
        "experience_assessment": "Project work demonstrates early-career experience.",
        "experience_highlights": ["Built a Python data project"],
        "learning_suggestions": ["Explore advanced Python testing."],
        "resume_improvements": [],
        "caveats": [],
    }
    result = ResumeAnalysis.from_dict(payload)
    assert result.skills[0].evidence == "Built a Python data project"


def test_model_response_missing_required_fields_is_rejected():
    with pytest.raises(ValueError):
        ResumeAnalysis.from_dict(
            {
                "summary": "Incomplete",
                "technical_skills": [],
                "soft_skills": [],
                "experience_assessment": "Assessment",
                "experience_highlights": [],
                "learning_suggestions": [],
            }
        )


def test_environment_selects_openai_gateway(monkeypatch):
    from app.config.settings import Settings

    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")

    settings = Settings.from_environment()

    assert settings.ai_provider == "openai"
    assert settings.openai_api_key == "synthetic-test-key"
