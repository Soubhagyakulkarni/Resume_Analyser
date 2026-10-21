"""Unit tests for group_skill_tiers()."""

from services.career_profile import group_skill_tiers
from services.skill_development_service import SkillDevelopmentStep


def _step(skill: str, listing_count: int) -> SkillDevelopmentStep:
    return SkillDevelopmentStep(
        skill=skill,
        roles=(),
        listing_count=listing_count,
        resource=None,
    )


class TestGroupSkillTiers:
    def test_empty_plan_returns_no_tiers(self):
        assert group_skill_tiers([]) == []

    def test_high_count_goes_to_start_now(self):
        tiers = group_skill_tiers([_step("Python", 5)])
        assert len(tiers) == 1
        assert tiers[0].label == "Start now"
        assert tiers[0].steps[0].skill == "Python"

    def test_count_two_goes_to_next(self):
        tiers = group_skill_tiers([_step("SQL", 2)])
        assert tiers[0].label == "Next"

    def test_count_one_goes_to_optional(self):
        tiers = group_skill_tiers([_step("Docker", 1)])
        assert tiers[0].label == "Optional"

    def test_mixed_counts_produce_all_three_tiers(self):
        plan = [_step("Python", 4), _step("SQL", 2), _step("Docker", 1)]
        tiers = group_skill_tiers(plan)
        labels = [t.label for t in tiers]
        assert "Start now" in labels
        assert "Next" in labels
        assert "Optional" in labels

    def test_tier_count_at_boundary_three_is_start_now(self):
        tiers = group_skill_tiers([_step("React", 3)])
        assert tiers[0].label == "Start now"

    def test_multiple_skills_in_same_tier(self):
        plan = [_step("A", 5), _step("B", 4)]
        tiers = group_skill_tiers(plan)
        assert len(tiers) == 1
        assert len(tiers[0].steps) == 2
