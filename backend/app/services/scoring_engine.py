"""
Scoring Engine — transparent, rule-based health dimension scoring.

Compares current check-in values against the user's personal rolling baseline.
Produces per-dimension deviation descriptions, NOT arbitrary 0-100 scores.

Dimensions: sleep, activity, hydration, stress, nutrition, recovery.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass
from app.schemas.schemas import DimensionScore, HealthDimensionEnum


@dataclass
class BaselineData:
    """Rolling averages computed from the user's recent check-ins."""
    avg_sleep_hours: Optional[float] = None
    avg_sleep_quality: Optional[float] = None
    avg_activity_minutes: Optional[float] = None
    avg_water_glasses: Optional[float] = None
    avg_stress_level: Optional[float] = None
    avg_meals_eaten: Optional[float] = None
    avg_meal_quality: Optional[float] = None
    avg_energy_level: Optional[float] = None
    avg_mood: Optional[float] = None
    days_of_data: int = 0


# ---------- Thresholds (transparent, not presented as medically precise) ----------

# These are rough lifestyle benchmarks for college students, not clinical standards.
MINIMUM_SLEEP_HOURS = 6.0
RECOMMENDED_SLEEP_HOURS = 7.5
MINIMUM_ACTIVITY_MINUTES = 20
RECOMMENDED_ACTIVITY_MINUTES = 30
MINIMUM_WATER_GLASSES = 4
RECOMMENDED_WATER_GLASSES = 8
HIGH_STRESS_THRESHOLD = 4  # on 1-5 scale
MINIMUM_MEALS = 2
RECOMMENDED_MEALS = 3


def compute_baseline(recent_checkins: List[dict], days: int = 7) -> BaselineData:
    """
    Compute rolling baseline from recent check-in data.

    Args:
        recent_checkins: list of check-in dicts (newest first), max `days` entries.

    Returns:
        BaselineData with averages.
    """
    if not recent_checkins:
        return BaselineData(days_of_data=0)

    data = recent_checkins[:days]
    n = len(data)

    def _avg(key: str) -> Optional[float]:
        vals = [d[key] for d in data if d.get(key) is not None]
        return sum(vals) / len(vals) if vals else None

    return BaselineData(
        avg_sleep_hours=_avg("sleep_hours"),
        avg_sleep_quality=_avg("sleep_quality"),
        avg_activity_minutes=_avg("activity_minutes"),
        avg_water_glasses=_avg("water_glasses"),
        avg_stress_level=_avg("stress_level"),
        avg_meals_eaten=_avg("meals_eaten"),
        avg_meal_quality=_avg("meal_quality"),
        avg_energy_level=_avg("energy_level"),
        avg_mood=_avg("mood"),
        days_of_data=n,
    )


def score_dimensions(
    current: dict,
    baseline: BaselineData,
    profile: Optional[dict] = None,
) -> List[DimensionScore]:
    """
    Score each health dimension by comparing current check-in to personal baseline.

    Returns a list of DimensionScore with plain-language deviation descriptions.
    No numeric scores are exposed to the user — only descriptive text.
    """
    scores: List[DimensionScore] = []

    # --- Sleep ---
    sleep_hours = current.get("sleep_hours")
    sleep_quality = current.get("sleep_quality")
    typical_sleep = (profile or {}).get("typical_sleep_hours", RECOMMENDED_SLEEP_HOURS)
    baseline_sleep = baseline.avg_sleep_hours or typical_sleep

    if sleep_hours is not None:
        if sleep_hours < MINIMUM_SLEEP_HOURS:
            desc = f"You reported {sleep_hours:.1f} hours of sleep, which is below the minimum threshold of {MINIMUM_SLEEP_HOURS} hours."
        elif sleep_hours < baseline_sleep * 0.8:
            desc = f"You reported {sleep_hours:.1f} hours of sleep, notably less than your recent average of {baseline_sleep:.1f} hours."
        elif sleep_hours >= baseline_sleep:
            desc = f"Your sleep ({sleep_hours:.1f} hours) is at or above your recent average."
        else:
            desc = f"Your sleep ({sleep_hours:.1f} hours) is slightly below your recent average of {baseline_sleep:.1f} hours."

        if sleep_quality is not None and sleep_quality <= 2:
            desc += f" You also rated your sleep quality as low ({sleep_quality}/5)."
    else:
        desc = "No sleep data reported today."

    scores.append(DimensionScore(
        dimension=HealthDimensionEnum.SLEEP,
        current_value=sleep_hours,
        baseline_value=baseline_sleep,
        deviation_description=desc,
    ))

    # --- Activity ---
    activity_min = current.get("activity_minutes")
    baseline_activity = baseline.avg_activity_minutes or float(RECOMMENDED_ACTIVITY_MINUTES)

    if activity_min is not None:
        if activity_min < MINIMUM_ACTIVITY_MINUTES:
            desc = f"You reported {activity_min} minutes of activity, below the {MINIMUM_ACTIVITY_MINUTES}-minute minimum."
        elif activity_min < baseline_activity * 0.7:
            desc = f"You reported {activity_min} minutes of activity, well below your recent average of {baseline_activity:.0f} minutes."
        elif activity_min >= baseline_activity:
            desc = f"Your activity ({activity_min} minutes) meets or exceeds your recent average."
        else:
            desc = f"Your activity ({activity_min} minutes) is slightly below your recent average of {baseline_activity:.0f} minutes."
    else:
        desc = "No activity data reported today."

    scores.append(DimensionScore(
        dimension=HealthDimensionEnum.ACTIVITY,
        current_value=float(activity_min) if activity_min is not None else None,
        baseline_value=baseline_activity,
        deviation_description=desc,
    ))

    # --- Hydration ---
    water = current.get("water_glasses")
    baseline_water = baseline.avg_water_glasses or float(RECOMMENDED_WATER_GLASSES)

    if water is not None:
        if water < MINIMUM_WATER_GLASSES:
            desc = f"You reported {water} glasses of water, below the minimum of {MINIMUM_WATER_GLASSES}."
        elif water < baseline_water * 0.7:
            desc = f"You reported {water} glasses of water, well below your recent average of {baseline_water:.1f}."
        elif water >= baseline_water:
            desc = f"Your hydration ({water} glasses) meets or exceeds your recent average."
        else:
            desc = f"Your hydration ({water} glasses) is slightly below your recent average of {baseline_water:.1f}."
    else:
        desc = "No hydration data reported today."

    scores.append(DimensionScore(
        dimension=HealthDimensionEnum.HYDRATION,
        current_value=float(water) if water is not None else None,
        baseline_value=baseline_water,
        deviation_description=desc,
    ))

    # --- Stress ---
    stress = current.get("stress_level")
    baseline_stress = baseline.avg_stress_level or 3.0  # neutral default

    if stress is not None:
        if stress >= HIGH_STRESS_THRESHOLD:
            desc = f"You rated your stress as {stress}/5, which is high."
            if baseline_stress < HIGH_STRESS_THRESHOLD:
                desc += f" This is above your recent average of {baseline_stress:.1f}/5."
        elif stress > baseline_stress * 1.3:
            desc = f"Your stress ({stress}/5) is noticeably higher than your recent average of {baseline_stress:.1f}/5."
        elif stress <= 2:
            desc = f"Your stress level ({stress}/5) is low — nice."
        else:
            desc = f"Your stress ({stress}/5) is around your typical level."
    else:
        desc = "No stress data reported today."

    scores.append(DimensionScore(
        dimension=HealthDimensionEnum.STRESS,
        current_value=float(stress) if stress is not None else None,
        baseline_value=baseline_stress,
        deviation_description=desc,
    ))

    # --- Nutrition ---
    meals = current.get("meals_eaten")
    meal_quality = current.get("meal_quality")
    baseline_meals = baseline.avg_meals_eaten or float(RECOMMENDED_MEALS)

    if meals is not None:
        if meals < MINIMUM_MEALS:
            desc = f"You reported only {meals} meal(s) today, below the minimum of {MINIMUM_MEALS}."
        elif meals < baseline_meals * 0.7:
            desc = f"You reported {meals} meal(s), fewer than your recent average of {baseline_meals:.1f}."
        else:
            desc = f"Your meal count ({meals}) is around your typical level."

        if meal_quality is not None and meal_quality <= 2:
            desc += f" You also rated your meal quality as low ({meal_quality}/5)."
    else:
        desc = "No nutrition data reported today."

    scores.append(DimensionScore(
        dimension=HealthDimensionEnum.NUTRITION,
        current_value=float(meals) if meals is not None else None,
        baseline_value=baseline_meals,
        deviation_description=desc,
    ))

    # --- Recovery (composite of energy + mood) ---
    energy = current.get("energy_level")
    mood = current.get("mood")
    baseline_energy = baseline.avg_energy_level or 3.0
    baseline_mood = baseline.avg_mood or 3.0

    parts = []
    recovery_current = None
    recovery_baseline = (baseline_energy + baseline_mood) / 2.0

    if energy is not None:
        recovery_current = float(energy)
        if energy <= 2:
            parts.append(f"Your energy level ({energy}/5) is low")
            if energy < baseline_energy * 0.7:
                parts[-1] += f", well below your average of {baseline_energy:.1f}/5"
        elif energy >= 4:
            parts.append(f"Your energy ({energy}/5) is good")
        else:
            parts.append(f"Your energy ({energy}/5) is moderate")

    if mood is not None:
        if recovery_current is not None:
            recovery_current = (recovery_current + float(mood)) / 2.0
        else:
            recovery_current = float(mood)
        if mood <= 2:
            parts.append(f"your mood ({mood}/5) is low")
            if mood < baseline_mood * 0.7:
                parts[-1] += f", below your average of {baseline_mood:.1f}/5"
        elif mood >= 4:
            parts.append(f"your mood ({mood}/5) is good")
        else:
            parts.append(f"your mood ({mood}/5) is moderate")

    if parts:
        desc = ". ".join(p.capitalize() if i == 0 else p for i, p in enumerate(parts)) + "."
    else:
        desc = "No energy or mood data reported today."

    scores.append(DimensionScore(
        dimension=HealthDimensionEnum.RECOVERY,
        current_value=recovery_current,
        baseline_value=recovery_baseline,
        deviation_description=desc,
    ))

    return scores
