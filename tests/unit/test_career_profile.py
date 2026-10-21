"""Unit tests for services.career_profile — career profile dataclass and helpers."""

from services.career_profile import CareerProfile


class TestCareerProfileDefaults:
    def test_all_fields_default_to_empty(self):
        profile = CareerProfile()
        assert profile.stage == ""
        assert profile.goal == ""
        assert profile.preferred_role == ""
        assert profile.preferred_location == ""

    def test_is_set_false_when_all_empty(self):
        assert not CareerProfile().is_set

    def test_is_set_true_when_any_field_provided(self):
        assert CareerProfile(stage="Student").is_set
        assert CareerProfile(goal="Internship").is_set
        assert CareerProfile(preferred_role="Data Analyst").is_set
        assert CareerProfile(preferred_location="Bengaluru").is_set


class TestFramingTag:
    def test_student_stage_returns_student(self):
        assert CareerProfile(stage="Student").framing_tag() == "student"

    def test_fresher_stage_returns_fresher(self):
        assert CareerProfile(stage="Fresher").framing_tag() == "fresher"

    def test_first_job_goal_returns_fresher(self):
        assert CareerProfile(goal="First job").framing_tag() == "fresher"

    def test_career_switch_goal_returns_career_switcher(self):
        assert CareerProfile(goal="Career switch").framing_tag() == "career-switcher"

    def test_experienced_stage_returns_experienced(self):
        assert CareerProfile(stage="Experienced").framing_tag() == "experienced"

    def test_upskilling_goal_returns_experienced(self):
        assert CareerProfile(goal="Upskilling").framing_tag() == "experienced"

    def test_empty_profile_returns_general(self):
        assert CareerProfile().framing_tag() == "general"


class TestEmphasisNote:
    def test_student_note_mentions_projects(self):
        note = CareerProfile(stage="Student").emphasis_note()
        assert "project" in note.lower()

    def test_fresher_note_mentions_transferable(self):
        note = CareerProfile(stage="Fresher").emphasis_note()
        assert "transferable" in note.lower()

    def test_career_switch_note_mentions_transition(self):
        note = CareerProfile(goal="Career switch").emphasis_note()
        assert "transition" in note.lower()

    def test_experienced_note_mentions_seniority(self):
        note = CareerProfile(stage="Experienced").emphasis_note()
        assert "seniority" in note.lower()

    def test_empty_profile_returns_general_note(self):
        note = CareerProfile().emphasis_note()
        assert "general" in note.lower()
