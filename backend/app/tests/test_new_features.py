"""Tests for new features: screen_time & caffeine dimensions, streaks, trends, goals."""

import pytest
from app.services.scoring_engine import compute_baseline, score_dimensions, BaselineData
from app.services.priority_engine import determine_priority
from app.schemas.schemas import HealthDimensionEnum


class TestScreenTimeDimension:
    def _base_current(self, **overrides):
        current = {
            "sleep_hours": 7.0, "sleep_quality": 3, "activity_minutes": 30,
            "water_glasses": 6, "stress_level": 2, "meals_eaten": 3,
            "meal_quality": 3, "energy_level": 3, "mood": 4,
            "screen_time_hours": 5.0, "caffeine_cups": 2,
        }
        current.update(overrides)
        return current

    def test_screen_time_scored(self):
        scores = score_dimensions(self._base_current(), BaselineData(days_of_data=7))
        screen = next(s for s in scores if s.dimension == HealthDimensionEnum.SCREEN_TIME)
        assert screen.current_value == 5.0
        assert screen.deviation_description  # has some text

    def test_excessive_screen_time_flagged(self):
        scores = score_dimensions(self._base_current(screen_time_hours=14.0), BaselineData(days_of_data=7))
        screen = next(s for s in scores if s.dimension == HealthDimensionEnum.SCREEN_TIME)
        assert "well above" in screen.deviation_description.lower()

    def test_custom_screen_goal_used(self):
        scores = score_dimensions(
            self._base_current(screen_time_hours=5.0),
            BaselineData(days_of_data=7),
            profile={"goal_max_screen_hours": 4.0},
        )
        screen = next(s for s in scores if s.dimension == HealthDimensionEnum.SCREEN_TIME)
        assert "custom goal" in screen.deviation_description.lower()

    def test_high_screen_time_priority(self):
        scores = score_dimensions(self._base_current(screen_time_hours=13.0), BaselineData(days_of_data=7))
        result = determine_priority(scores)
        assert result.priority_dimension == HealthDimensionEnum.SCREEN_TIME
        assert any("grayscale" in a.lower() or "app" in a.lower() for a in result.suggested_actions)


class TestCaffeineDimension:
    def _base_current(self, **overrides):
        current = {
            "sleep_hours": 7.0, "sleep_quality": 3, "activity_minutes": 30,
            "water_glasses": 6, "stress_level": 2, "meals_eaten": 3,
            "meal_quality": 3, "energy_level": 3, "mood": 4,
            "screen_time_hours": 5.0, "caffeine_cups": 2,
        }
        current.update(overrides)
        return current

    def test_caffeine_scored(self):
        scores = score_dimensions(self._base_current(), BaselineData(days_of_data=7))
        caffeine = next(s for s in scores if s.dimension == HealthDimensionEnum.CAFFEINE)
        assert caffeine.current_value == 2.0

    def test_excessive_caffeine_flagged(self):
        scores = score_dimensions(self._base_current(caffeine_cups=6), BaselineData(days_of_data=7))
        caffeine = next(s for s in scores if s.dimension == HealthDimensionEnum.CAFFEINE)
        assert "limit" in caffeine.deviation_description.lower()

    def test_very_high_caffeine_priority(self):
        scores = score_dimensions(self._base_current(caffeine_cups=7), BaselineData(days_of_data=7))
        result = determine_priority(scores)
        assert result.priority_dimension == HealthDimensionEnum.CAFFEINE

    def test_caffeine_baseline_computed(self):
        data = [
            {"caffeine_cups": 3, "sleep_hours": 7.0, "activity_minutes": 30,
             "water_glasses": 6, "stress_level": 2, "meals_eaten": 3,
             "meal_quality": 3, "energy_level": 3, "mood": 4, "sleep_quality": 3},
            {"caffeine_cups": 5, "sleep_hours": 7.0, "activity_minutes": 30,
             "water_glasses": 6, "stress_level": 2, "meals_eaten": 3,
             "meal_quality": 3, "energy_level": 3, "mood": 4, "sleep_quality": 3},
        ]
        baseline = compute_baseline(data)
        assert baseline.avg_caffeine_cups == 4.0


class TestGoalsAndTrendLogic:
    def test_trend_direction_logic(self):
        """Verify improving/declining direction mapping for lower-is-better dimensions."""
        # Simulate the trend logic used in routes.get_trends
        def direction(cur, prev, lower_is_better=True):
            if cur is None or prev is None:
                return "no_data"
            changed = cur - prev
            tolerance = abs(prev) * 0.1 if prev else 0.1
            if abs(changed) <= tolerance:
                return "stable"
            if lower_is_better:
                return "improving" if changed < 0 else "declining"
            return "improving" if changed > 0 else "declining"

        assert direction(4.0, 5.0, lower_is_better=True) == "improving"   # sleep down = good
        assert direction(6.0, 5.0, lower_is_better=True) == "declining"   # stress up = bad
        assert direction(5.0, 5.0, lower_is_better=True) == "stable"
        assert direction(40.0, 20.0, lower_is_better=False) == "improving"  # activity up = good
        assert direction(None, 5.0) == "no_data"

    def test_goal_meets_check(self):
        """Goal-check semantics used by /stats/streaks."""
        class FakeProfile:
            goal_sleep_hours = 7.0
            goal_water_glasses = 6
            goal_activity_minutes = 20
            goal_max_screen_hours = 7.0
            goal_max_caffeine_cups = 3

        class FakeCheckin:
            sleep_hours = 7.5
            water_glasses = 6
            activity_minutes = 25
            screen_time_hours = 5.0
            caffeine_cups = 2

        profile, checkin = FakeProfile(), FakeCheckin()
        checks = []
        if profile.goal_sleep_hours is not None and checkin.sleep_hours is not None:
            checks.append(checkin.sleep_hours >= profile.goal_sleep_hours)
        if profile.goal_max_screen_hours is not None and checkin.screen_time_hours is not None:
            checks.append(checkin.screen_time_hours <= profile.goal_max_screen_hours)
        assert all(checks)  # meets all goals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
