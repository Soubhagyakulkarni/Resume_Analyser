"""Tests for model-response and evidence validation."""

import pytest

from models.analysis import ImprovementSuggestion, ResumeAnalysis, Skill
from services.analysis_service import AnalysisService


class FakeGateway:
    def __init__(self, result: ResumeAnalysis) -> None:
        self.result = result

    def analyze(self, resume_text: str) -> ResumeAnalysis:
        return self.result


def test_accepts_skill_with_exact_resume_evidence(sample_analysis):
    result = AnalysisService(FakeGateway(sample_analysis)).analyze("Built a Python data project")
    assert result == sample_analysis


def test_downgrades_skill_to_inferred_when_evidence_has_low_overlap(sample_analysis):
    """Skills whose stated evidence has low resume overlap are marked inferred, not rejected.

    This preserves the full analysis while correctly labelling uncertain evidence,
    per PRD FR-14: inferred skills must be labelled, not silently dropped.
    """
    service = AnalysisService(FakeGateway(sample_analysis))
    # Resume text shares no meaningful tokens with the skill evidence "Built a Python data project"
    result = service.analyze("Created a dashboard using a different language")
    # The skill should survive but be downgraded to inferred
    assert len(result.technical_skills) == 1
    assert result.technical_skills[0].name == "Python"
    assert result.technical_skills[0].inferred is True


def test_accepts_evidence_with_intervening_resume_words(sample_analysis):
    result = AnalysisService(FakeGateway(sample_analysis)).analyze(
        "Built a Python data project using pandas and SQL"
    )
    assert result.skills[0].name == "Python"


def test_normalizes_model_empty_evidence_sentinel():
    analysis = ResumeAnalysis.from_dict(
        {
            "summary": "Summary",
            "technical_skills": [],
            "soft_skills": [],
            "experience_assessment": "Assessment",
            "experience_highlights": [],
            "learning_suggestions": [],
            "resume_improvements": [
                {
                    "priority": "low",
                    "issue": "Improve layout",
                    "recommendation": "Use consistent spacing",
                    "evidence": "empty string",
                }
            ],
        }
    )
    assert analysis.resume_improvements[0].evidence == ""


def test_analysis_model_rejects_unbounded_or_malformed_response():
    with pytest.raises(ValueError):
        ResumeAnalysis.from_dict(
            {
                "summary": "x" * 4001,
                "technical_skills": [],
                "soft_skills": [],
                "experience_assessment": "Assessment",
                "experience_highlights": [],
                "learning_suggestions": [],
                "resume_improvements": [],
            }
        )


def test_analysis_model_rejects_non_boolean_inferred_flag():
    with pytest.raises(TypeError):
        ResumeAnalysis.from_dict(
            {
                "summary": "Summary",
                "technical_skills": [{"name": "Python", "evidence": "quote", "inferred": "false"}],
                "soft_skills": [],
                "experience_assessment": "Assessment",
                "experience_highlights": [],
                "learning_suggestions": [],
                "resume_improvements": [],
            }
        )


def test_clears_suggestion_evidence_when_overlap_is_low():
    """Suggestion evidence with low resume overlap is cleared, not treated as fatal.

    The suggestion (issue + recommendation) is preserved; only the unsupported
    evidence reference is removed so the user still sees useful feedback.
    """
    analysis = ResumeAnalysis(
        summary="Summary",
        technical_skills=(),
        soft_skills=(),
        experience_assessment="Assessment",
        experience_highlights=(),
        learning_suggestions=(),
        resume_improvements=(
            ImprovementSuggestion(
                priority="medium",
                issue="Add quantified achievements",
                recommendation="Use metrics to strengthen impact",
                evidence="some fabricated phrase not in resume",
            ),
        ),
    )
    # Resume text shares no tokens with the suggestion evidence
    result = AnalysisService(FakeGateway(analysis)).analyze("Worked on projects at company")
    assert len(result.resume_improvements) == 1
    assert result.resume_improvements[0].issue == "Add quantified achievements"
    assert result.resume_improvements[0].evidence == ""  # cleared, not crash


def test_analysis_logs_do_not_include_resume_derived_text(caplog):
    analysis = ResumeAnalysis(
        summary="Synthetic summary",
        technical_skills=(
            Skill(
                "SyntheticPrivateSkill",
                "UNIQUE_PRIVATE_RESUME_EVIDENCE_7821",
                False,
            ),
        ),
        soft_skills=(),
        experience_assessment="Synthetic assessment",
        experience_highlights=(),
        learning_suggestions=(),
        resume_improvements=(),
    )

    AnalysisService(FakeGateway(analysis)).analyze("Different source content")

    assert "UNIQUE_PRIVATE_RESUME_EVIDENCE_7821" not in caplog.text
    assert "SyntheticPrivateSkill" not in caplog.text
