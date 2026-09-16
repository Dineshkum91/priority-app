"""
Tests for the Safety Layer.

Demonstrates that the safety layer intercepts red-flag inputs
BEFORE they reach the priority engine.
"""

import pytest
from app.services.safety_layer import check_safety


class TestCrisisKeywordDetection:
    """Test that crisis-related language in notes triggers a safety flag."""

    def test_suicidal_ideation_flagged(self):
        checkin = {"notes": "I just want to die, everything is too much"}
        result = check_safety(checkin)
        assert result.is_flagged is True
        assert "Crisis-related language" in result.flag_reason
        assert result.support_message is not None
        assert "988" in result.support_message

    def test_self_harm_mention_flagged(self):
        checkin = {"notes": "I've been cutting myself again"}
        result = check_safety(checkin)
        assert result.is_flagged is True
        assert "Crisis-related language" in result.flag_reason

    def test_normal_notes_not_flagged(self):
        checkin = {"notes": "Had a tough day but feeling okay. Went for a walk."}
        result = check_safety(checkin)
        assert result.is_flagged is False


class TestDisorderedEatingDetection:
    """Test that disordered-eating language triggers a safety flag."""

    def test_purging_mention_flagged(self):
        checkin = {"notes": "I've been purging after meals"}
        result = check_safety(checkin)
        assert result.is_flagged is True
        assert "disordered eating" in result.flag_reason.lower()

    def test_restriction_mention_flagged(self):
        checkin = {"notes": "I'm starving myself to lose weight"}
        result = check_safety(checkin)
        assert result.is_flagged is True

    def test_normal_diet_notes_not_flagged(self):
        checkin = {"notes": "Trying to eat healthier, had a salad for lunch"}
        result = check_safety(checkin)
        assert result.is_flagged is False


class TestExtremeSleepDeprivation:
    """Test that repeated extreme sleep deprivation is caught."""

    def test_three_consecutive_extreme_nights_flagged(self):
        current = {"sleep_hours": 1.5, "notes": None}
        recent = [
            {"sleep_hours": 2.0, "notes": None},
            {"sleep_hours": 1.0, "notes": None},
            {"sleep_hours": 6.0, "notes": None},  # before that was fine
        ]
        result = check_safety(current, recent)
        assert result.is_flagged is True
        assert "sleep deprivation" in result.flag_reason.lower()

    def test_single_bad_night_not_flagged(self):
        current = {"sleep_hours": 2.0, "notes": None}
        recent = [
            {"sleep_hours": 7.0, "notes": None},
            {"sleep_hours": 6.5, "notes": None},
        ]
        result = check_safety(current, recent)
        assert result.is_flagged is False

    def test_zero_sleep_warning(self):
        current = {"sleep_hours": 0, "notes": None}
        recent = []
        result = check_safety(current, recent)
        assert result.is_flagged is True  # 0 hours is always concerning
        assert "Zero hours" in result.flag_reason


class TestSustainedMaxStress:
    """Test that sustained maximum stress triggers a flag."""

    def test_five_days_max_stress_flagged(self):
        current = {"stress_level": 5, "notes": None}
        recent = [
            {"stress_level": 5, "notes": None},
            {"stress_level": 5, "notes": None},
            {"stress_level": 5, "notes": None},
            {"stress_level": 5, "notes": None},
        ]
        result = check_safety(current, recent)
        assert result.is_flagged is True
        assert "stress" in result.flag_reason.lower()

    def test_moderate_stress_not_flagged(self):
        current = {"stress_level": 4, "notes": None}
        recent = [{"stress_level": 3, "notes": None}] * 5
        result = check_safety(current, recent)
        assert result.is_flagged is False


class TestConsecutiveNoMeals:
    """Test that reporting zero meals for multiple days is flagged."""

    def test_two_days_no_meals_flagged(self):
        current = {"meals_eaten": 0, "notes": None}
        recent = [{"meals_eaten": 0, "notes": None}]
        result = check_safety(current, recent)
        assert result.is_flagged is True
        assert "meals" in result.flag_reason.lower()

    def test_one_skipped_day_not_flagged(self):
        current = {"meals_eaten": 0, "notes": None}
        recent = [{"meals_eaten": 2, "notes": None}]
        result = check_safety(current, recent)
        assert result.is_flagged is False


class TestSafetyGateIntegrity:
    """Test that the safety layer's output format is correct for downstream use."""

    def test_flagged_result_contains_support_resources(self):
        checkin = {"notes": "I want to kill myself"}
        result = check_safety(checkin)
        assert result.is_flagged is True
        assert result.support_message is not None
        assert "988" in result.support_message
        assert "campus counselling" in result.support_message.lower()

    def test_clean_result_has_no_support_message(self):
        checkin = {"sleep_hours": 7, "stress_level": 2, "meals_eaten": 3, "notes": "Great day!"}
        result = check_safety(checkin)
        assert result.is_flagged is False
        assert result.flag_reason is None
        assert result.support_message is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
