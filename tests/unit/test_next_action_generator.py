"""Unit tests for generate_next_actions()."""

from __future__ import annotations

from datetime import UTC, datetime

from models.analysis import ImprovementSuggestion, ResumeAnalysis, Skill
from models.job import Job, JobRecommendation
from services.career_profile import NextAction, generate_next_actions
from services.resume_quality_service import ResumeQualityFinding, ResumeQualityReport
from services.skill_development_service import SkillDevelopmentStep

# ---------------------------------------------------------------------------
# Synthetic helpers
# ---------------------------------------------------------------------------


def _analysis(
    suggestions: tuple[ImprovementSuggestion, ...] = (),
    learning_suggestions: tuple[str, ...] = (),
) -> ResumeAnalysis:
    return ResumeAnalysis(
        summary="summary",
        technical_skills=(Skill("Python", "Built a project", False),),
        soft_skills=(),
        experience_assessment="assessment",
        experience_highlights=(),
        learning_suggestions=learning_suggestions,
        resume_improvements=suggestions,
    )


def _suggestion(priority: str = "high") -> ImprovementSuggestion:
    return ImprovementSuggestion(
        priority=priority,
        issue="Add quantified achievements",
        recommendation="Include numbers to show impact.",
        evidence="",
    )


def _recommendation(missing: tuple[str, ...] = ("SQL", "Docker")) -> JobRecommendation:
    job = Job(
        id="j1",
        title="Data Analyst",
        description="desc",
        required_skills=("Python",) + missing,
        location="Remote",
        application_url="https://example.invalid/apply",
        source="Test",
        updated_at=datetime.now(UTC).date(),
    )
    return JobRecommendation(
        job=job,
        matched_skills=("Python",),
        missing_from_resume=missing,
        match_ratio=0.5,
        rationale="rationale",
    )


def _step(skill: str = "Docker", listing_count: int = 3) -> SkillDevelopmentStep:
    return SkillDevelopmentStep(
        skill=skill,
        roles=("Data Analyst",),
        listing_count=listing_count,
        resource=None,
    )


def _quality_report(review_count: int = 1) -> ResumeQualityReport:
    findings = tuple(
        ResumeQualityFinding(title=f"Check {i}", status="Review", detail="d", suggestion="s")
        for i in range(review_count)
    )
    return ResumeQualityReport(findings=findings, compared_listing_count=0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGenerateNextActions:
    def test_empty_inputs_returns_explore_fallback(self):
        actions = generate_next_actions(_analysis(), [], [], None)
        assert len(actions) >= 1
        assert any("explore" in a.title.lower() for a in actions)

    def test_high_priority_suggestion_included_first(self):
        suggestion = _suggestion("high")
        actions = generate_next_actions(_analysis(suggestions=(suggestion,)), [], [], None)
        assert actions[0].section == "Resume Insights"
        assert actions[0].priority == "High"

    def test_medium_suggestion_not_included_when_high_exists_first(self):
        """High-priority action beats medium-priority suggestion for first slot."""
        high = _suggestion("high")
        actions = generate_next_actions(_analysis(suggestions=(high,)), [], [], None, max_actions=1)
        assert len(actions) == 1
        assert actions[0].priority == "High"

    def test_missing_skills_from_recommendation_added(self):
        rec = _recommendation(missing=("SQL", "Docker"))
        actions = generate_next_actions(_analysis(), [rec], [], None)
        job_action = next((a for a in actions if a.section == "Job Recommendations"), None)
        assert job_action is not None

    def test_skill_plan_step_added(self):
        step = _step("Docker", 4)
        actions = generate_next_actions(_analysis(), [], [step], None)
        skill_action = next((a for a in actions if a.section == "Skill Development Plan"), None)
        assert skill_action is not None
        assert "Docker" in skill_action.title

    def test_quality_review_finding_added(self):
        report = _quality_report(review_count=1)
        actions = generate_next_actions(_analysis(), [], [], report)
        check_action = next((a for a in actions if a.section == "Resume Quality Checks"), None)
        assert check_action is not None

    def test_max_actions_respected(self):
        for max_n in (1, 2, 3):
            actions = generate_next_actions(
                _analysis(suggestions=(_suggestion(),)),
                [_recommendation()],
                [_step()],
                _quality_report(),
                max_actions=max_n,
            )
            assert len(actions) <= max_n

    def test_actions_are_next_action_instances(self):
        actions = generate_next_actions(
            _analysis(suggestions=(_suggestion(),)),
            [_recommendation()],
            [_step()],
            _quality_report(),
        )
        for action in actions:
            assert isinstance(action, NextAction)

    def test_high_count_skill_gets_high_priority(self):
        step = _step("SQL", listing_count=5)
        actions = generate_next_actions(_analysis(), [], [step], None)
        skill_action = next((a for a in actions if "Skill Development" in a.section), None)
        assert skill_action is not None
        assert skill_action.priority == "High"

    def test_low_count_skill_gets_medium_priority(self):
        step = _step("CSS", listing_count=1)
        actions = generate_next_actions(_analysis(), [], [step], None)
        skill_action = next((a for a in actions if "Skill Development" in a.section), None)
        assert skill_action is not None
        assert skill_action.priority == "Medium"
