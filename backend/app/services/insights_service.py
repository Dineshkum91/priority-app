"""
Insights Service — computes weekly insights only when ≥7 days of data exist.

Never fabricates percentages or patterns from insufficient data.
"""

import json
from datetime import date, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.models import DailyHealthData, HealthInsight
from app.schemas.schemas import WeeklyInsightsResponse, HealthInsightResponse


def compute_weekly_insight(
    db: Session,
    user_id,
    week_start: Optional[date] = None,
) -> WeeklyInsightsResponse:
    """
    Compute or retrieve weekly insights for a user.

    Returns a WeeklyInsightsResponse that clearly indicates if data is sufficient.
    """
    if week_start is None:
        # Default to the current week (Monday start)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    week_end = week_start + timedelta(days=6)

    # Query check-ins for this week
    checkins = (
        db.query(DailyHealthData)
        .filter(
            DailyHealthData.user_id == user_id,
            DailyHealthData.check_in_date >= week_start,
            DailyHealthData.check_in_date <= week_end,
        )
        .order_by(DailyHealthData.check_in_date)
        .all()
    )

    days_with_data = len(checkins)

    if days_with_data < 7:
        return WeeklyInsightsResponse(
            has_sufficient_data=False,
            message=(
                f"Not enough data yet — you have {days_with_data} day(s) of check-ins this week. "
                f"Complete 7 days for weekly insights."
            ),
            insight=None,
        )

    # Compute averages
    def _safe_avg(values):
        filtered = [v for v in values if v is not None]
        return round(sum(filtered) / len(filtered), 1) if filtered else None

    avg_sleep = _safe_avg([c.sleep_hours for c in checkins])
    avg_activity = _safe_avg([c.activity_minutes for c in checkins])
    avg_water = _safe_avg([c.water_glasses for c in checkins])
    avg_stress = _safe_avg([c.stress_level for c in checkins])
    avg_meals = _safe_avg([c.meals_eaten for c in checkins])
    avg_energy = _safe_avg([c.energy_level for c in checkins])
    avg_mood = _safe_avg([c.mood for c in checkins])

    # Detect simple patterns (only claim what data supports)
    patterns = _detect_patterns(checkins)

    # Upsert insight
    existing = (
        db.query(HealthInsight)
        .filter(
            HealthInsight.user_id == user_id,
            HealthInsight.week_start == week_start,
        )
        .first()
    )

    if existing:
        existing.avg_sleep_hours = avg_sleep
        existing.avg_activity_minutes = avg_activity
        existing.avg_water_glasses = avg_water
        existing.avg_stress_level = avg_stress
        existing.avg_meals_eaten = avg_meals
        existing.avg_energy_level = avg_energy
        existing.avg_mood = avg_mood
        existing.patterns = json.dumps(patterns) if patterns else None
        existing.days_with_data = days_with_data
        insight = existing
    else:
        insight = HealthInsight(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            avg_sleep_hours=avg_sleep,
            avg_activity_minutes=avg_activity,
            avg_water_glasses=avg_water,
            avg_stress_level=avg_stress,
            avg_meals_eaten=avg_meals,
            avg_energy_level=avg_energy,
            avg_mood=avg_mood,
            patterns=json.dumps(patterns) if patterns else None,
            days_with_data=days_with_data,
        )
        db.add(insight)

    db.commit()
    db.refresh(insight)

    # Build summary message from the data
    summary_parts = []
    if avg_sleep is not None:
        summary_parts.append(f"You averaged {avg_sleep} hours of sleep this week")
    if avg_stress is not None:
        summary_parts.append(f"your average stress level was {avg_stress}/5")
    if avg_mood is not None:
        summary_parts.append(f"your average mood was {avg_mood}/5")

    summary = ". ".join(summary_parts) + "." if summary_parts else "Weekly data has been recorded."
    if patterns:
        summary += " Patterns observed: " + "; ".join(patterns) + "."

    return WeeklyInsightsResponse(
        has_sufficient_data=True,
        message=summary,
        insight=HealthInsightResponse.model_validate(insight),
    )


def _detect_patterns(checkins) -> List[str]:
    """
    Detect simple patterns from a week of data.
    Only claim observations that are directly supported by the data.
    """
    patterns = []

    # Sleep trend
    sleep_vals = [c.sleep_hours for c in checkins if c.sleep_hours is not None]
    if len(sleep_vals) >= 5:
        first_half = sleep_vals[:len(sleep_vals) // 2]
        second_half = sleep_vals[len(sleep_vals) // 2:]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        if avg_second > avg_first * 1.15:
            patterns.append("Your sleep hours increased over the course of the week")
        elif avg_second < avg_first * 0.85:
            patterns.append("Your sleep hours decreased over the course of the week")

    # Stress-energy correlation
    stress_vals = [c.stress_level for c in checkins if c.stress_level is not None]
    energy_vals = [c.energy_level for c in checkins if c.energy_level is not None]
    if len(stress_vals) >= 5 and len(energy_vals) >= 5:
        high_stress_days = sum(1 for s in stress_vals if s >= 4)
        low_energy_days = sum(1 for e in energy_vals if e <= 2)
        if high_stress_days >= 3 and low_energy_days >= 3:
            patterns.append(
                "You had several high-stress days that coincided with low energy — "
                "stress may be affecting your overall energy"
            )

    # Hydration consistency
    water_vals = [c.water_glasses for c in checkins if c.water_glasses is not None]
    if len(water_vals) >= 5:
        low_water_days = sum(1 for w in water_vals if w <= 3)
        if low_water_days >= 4:
            patterns.append(
                "Hydration was consistently low this week (4+ days below 4 glasses)"
            )

    # Meal skipping
    meal_vals = [c.meals_eaten for c in checkins if c.meals_eaten is not None]
    if len(meal_vals) >= 5:
        skip_days = sum(1 for m in meal_vals if m <= 1)
        if skip_days >= 3:
            patterns.append(
                "You ate 1 or fewer meals on several days this week"
            )

    return patterns
