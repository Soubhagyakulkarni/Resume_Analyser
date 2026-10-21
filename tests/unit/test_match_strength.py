"""Unit tests for classify_match_strength()."""

from services.career_profile import classify_match_strength


class TestClassifyMatchStrength:
    def test_ratio_1_is_strong(self):
        assert classify_match_strength(1.0) == "Strong"

    def test_ratio_at_strong_threshold_is_strong(self):
        assert classify_match_strength(0.70) == "Strong"

    def test_ratio_just_below_strong_is_moderate(self):
        assert classify_match_strength(0.69) == "Moderate"

    def test_ratio_at_moderate_threshold_is_moderate(self):
        assert classify_match_strength(0.40) == "Moderate"

    def test_ratio_just_below_moderate_is_exploratory(self):
        assert classify_match_strength(0.39) == "Exploratory"

    def test_ratio_zero_is_exploratory(self):
        assert classify_match_strength(0.0) == "Exploratory"

    def test_ratio_half_is_moderate(self):
        assert classify_match_strength(0.50) == "Moderate"
