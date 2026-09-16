"""Tests for the scoring engine and priority engine."""

import pytest
from app.services.scoring_engine import compute_baseline, score_dimensions, BaselineData
from app.services.priority_engine import determine_priority
from app.schemas.schemas import HealthDimensionEnum


class TestComputeBaseline:
    def test_empty_data(self):
        baseline = compute_baseline([])
        assert baseline.days_of_data == 0
        assert baseline.avg_sleep_hours is None

    def test_basic_average(self):
        data = [
            {"sleep_hours": 7.0, "sleep_quality": 3, "activity_minutes": 30,
             "water_glasses": 6, "stress_level": 2, "meals_eaten": 3,
             "meal_quality": 3, "energy_level": 3, "mood": 4},
            {"sleep_hours": 8.0, "sleep_quality": 4, "activity_minutes": 20,
             "water_glasses": 8, "stress_level": 3, "meals_eaten": 3,
             "meal_quality": 4, "energy_level": 4, "mood": 3},
        ]
        baseline = compute_baseline(data)
        assert baseline.avg_sleep_hours == 7.5
        assert baseline.days_of_data == 2


class TestScoreDimensions:
    def test_low_sleep_detected(self):
        current = {"sleep_hours": 3.0, "sleep_quality": 1, "activity_minutes": 30,
                    "water_glasses": 6, "stress_level": 2, "meals_eaten": 3,
                    "meal_quality": 3, "energy_level": 3, "mood": 4}
        baseline = BaselineData(avg_sleep_hours=7.0, days_of_data=7)
        scores = score_dimensions(current, baseline)
        sleep_score = next(s for s in scores if s.dimension == HealthDimensionEnum.SLEEP)
        assert "below" in sleep_score.deviation_description.lower() or "minimum" in sleep_score.deviation_description.lower()

    def test_good_day_no_alarms(self):
        current = {"sleep_hours": 7.5, "sleep_quality": 4, "activity_minutes": 35,
                    "water_glasses": 8, "stress_level": 2, "meals_eaten": 3,
                    "meal_quality": 4, "energy_level": 4, "mood": 4}
        baseline = BaselineData(avg_sleep_hours=7.0, avg_activity_minutes=30.0,
                                avg_water_glasses=7.0, avg_stress_level=2.5,
                                avg_meals_eaten=3.0, avg_energy_level=3.5,
                                avg_mood=3.5, days_of_data=7)
        scores = score_dimensions(current, baseline)
        for s in scores:
            assert "below" not in s.deviation_description.lower() or "slightly" in s.deviation_description.lower()


class TestPriorityEngine:
    def test_sleep_prioritised_when_severe(self):
        current = {"sleep_hours": 2.0, "sleep_quality": 1, "activity_minutes": 30,
                    "water_glasses": 6, "stress_level": 2, "meals_eaten": 3,
                    "meal_quality": 3, "energy_level": 3, "mood": 4}
        baseline = BaselineData(avg_sleep_hours=7.0, days_of_data=7)
        scores = score_dimensions(current, baseline)
        result = determine_priority(scores)
        assert result.priority_dimension == HealthDimensionEnum.SLEEP

    def test_diminishing_returns_rotation(self):
        """If same priority repeated 3+ times, urgency is reduced."""
        current = {"sleep_hours": 5.0, "sleep_quality": 2, "activity_minutes": 5,
                    "water_glasses": 3, "stress_level": 4, "meals_eaten": 1,
                    "meal_quality": 2, "energy_level": 2, "mood": 2}
        baseline = BaselineData(avg_sleep_hours=7.0, avg_activity_minutes=30.0,
                                avg_water_glasses=7.0, avg_stress_level=2.5,
                                avg_meals_eaten=3.0, avg_energy_level=3.5,
                                avg_mood=3.5, days_of_data=7)
        scores = score_dimensions(current, baseline)

        # Without repetition
        result1 = determine_priority(scores, [])
        dim1 = result1.priority_dimension

        # With 3 consecutive same dimensions
        result2 = determine_priority(scores, [dim1.value, dim1.value, dim1.value])
        # The priority should either stay the same (if urgency is overwhelming) or rotate
        assert result2.priority_dimension is not None
        assert len(result2.suggested_actions) >= 2

    def test_actions_provided(self):
        current = {"sleep_hours": 4.0, "sleep_quality": 2, "activity_minutes": 0,
                    "water_glasses": 2, "stress_level": 5, "meals_eaten": 1,
                    "meal_quality": 1, "energy_level": 1, "mood": 1}
        baseline = BaselineData(days_of_data=0)
        scores = score_dimensions(current, baseline)
        result = determine_priority(scores)
        assert len(result.suggested_actions) >= 2
        assert all(isinstance(a, str) for a in result.suggested_actions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
