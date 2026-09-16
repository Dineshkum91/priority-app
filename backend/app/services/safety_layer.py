"""
Safety Layer — runs BEFORE the priority engine on every check-in.

Detects red-flag inputs and suppresses normal recommendations when triggered.
This layer CANNOT be overridden by the priority/recommendation logic.

Detection categories:
1. Extreme sleep deprivation (repeated)
2. Disordered-eating language in notes
3. Self-harm / crisis mentions in notes
4. Severe symptom patterns
"""

import re
from typing import Optional, List
from dataclasses import dataclass
from app.schemas.schemas import SafetyCheckResult


# ---------- Configuration ----------

# Keywords and phrases that trigger safety flags (case-insensitive)
CRISIS_KEYWORDS = [
    # Self-harm / suicidal ideation
    "kill myself", "want to die", "end it all", "suicide", "suicidal",
    "self-harm", "self harm", "cutting myself", "hurt myself",
    "don't want to be alive", "no reason to live", "better off dead",
    # Severe distress
    "can't go on", "can't take it anymore", "give up on everything",
]

DISORDERED_EATING_KEYWORDS = [
    "purging", "purge", "binge and purge", "making myself throw up",
    "throwing up on purpose", "laxatives to lose weight",
    "haven't eaten in days", "starving myself", "restricting food",
    "scared to eat", "afraid of food", "don't deserve to eat",
]

# Thresholds for pattern-based flags
EXTREME_SLEEP_DEPRIVATION_HOURS = 2.0  # ≤2 hours
CONSECUTIVE_DAYS_THRESHOLD = 3  # flagged if repeated N days
MAX_STRESS_LEVEL = 5  # max scale value
CONSECUTIVE_MAX_STRESS_DAYS = 5

SUPPORT_RESOURCES = (
    "It sounds like you may be going through a really tough time. "
    "You don't have to handle this alone.\n\n"
    "• **988 Suicide & Crisis Lifeline**: Call or text 988 (US)\n"
    "• **Crisis Text Line**: Text HOME to 741741\n"
    "• **Your campus counselling centre** — most offer free, confidential support\n\n"
    "Priority is not a substitute for professional support. "
    "Please reach out to someone who can help."
)


@dataclass
class _FlagDetail:
    reason: str
    severity: str  # "critical" or "warning"


def check_safety(
    current_checkin: dict,
    recent_checkins: Optional[List[dict]] = None,
) -> SafetyCheckResult:
    """
    Run safety checks on the current check-in data.

    Args:
        current_checkin: dict with keys matching DailyCheckInCreate fields
        recent_checkins: list of the last N check-ins (dicts), newest first

    Returns:
        SafetyCheckResult with is_flagged=True if any red flag is detected.
    """
    flags: List[_FlagDetail] = []

    # 1. Check notes for crisis keywords
    notes = (current_checkin.get("notes") or "").lower()
    if notes:
        for keyword in CRISIS_KEYWORDS:
            if keyword in notes:
                flags.append(_FlagDetail(
                    reason=f"Crisis-related language detected in check-in notes.",
                    severity="critical",
                ))
                break  # one match is enough

        for keyword in DISORDERED_EATING_KEYWORDS:
            if keyword in notes:
                flags.append(_FlagDetail(
                    reason="Language related to disordered eating detected in check-in notes.",
                    severity="critical",
                ))
                break

    # 2. Check for extreme sleep deprivation pattern
    sleep_hours = current_checkin.get("sleep_hours")
    if sleep_hours is not None and sleep_hours <= EXTREME_SLEEP_DEPRIVATION_HOURS:
        # Check if this is a pattern (consecutive days)
        if recent_checkins:
            consecutive_extreme = 1  # counting today
            for past in recent_checkins:
                past_sleep = past.get("sleep_hours")
                if past_sleep is not None and past_sleep <= EXTREME_SLEEP_DEPRIVATION_HOURS:
                    consecutive_extreme += 1
                else:
                    break  # pattern broken
            if consecutive_extreme >= CONSECUTIVE_DAYS_THRESHOLD:
                flags.append(_FlagDetail(
                    reason=(
                        f"Extreme sleep deprivation reported for {consecutive_extreme} "
                        f"consecutive days (≤{EXTREME_SLEEP_DEPRIVATION_HOURS} hours each)."
                    ),
                    severity="critical",
                ))
        # Even a single night of 0 hours is concerning
        if sleep_hours == 0:
            flags.append(_FlagDetail(
                reason="Zero hours of sleep reported.",
                severity="warning",
            ))

    # 3. Check for sustained maximum stress
    stress_level = current_checkin.get("stress_level")
    if stress_level is not None and stress_level >= MAX_STRESS_LEVEL:
        if recent_checkins:
            consecutive_max_stress = 1
            for past in recent_checkins:
                past_stress = past.get("stress_level")
                if past_stress is not None and past_stress >= MAX_STRESS_LEVEL:
                    consecutive_max_stress += 1
                else:
                    break
            if consecutive_max_stress >= CONSECUTIVE_MAX_STRESS_DAYS:
                flags.append(_FlagDetail(
                    reason=(
                        f"Maximum stress level reported for {consecutive_max_stress} "
                        f"consecutive days."
                    ),
                    severity="critical",
                ))

    # 4. Check for zero meals over multiple days (potential disordered eating pattern)
    meals = current_checkin.get("meals_eaten")
    if meals is not None and meals == 0:
        if recent_checkins:
            consecutive_no_meals = 1
            for past in recent_checkins:
                past_meals = past.get("meals_eaten")
                if past_meals is not None and past_meals == 0:
                    consecutive_no_meals += 1
                else:
                    break
            if consecutive_no_meals >= 2:
                flags.append(_FlagDetail(
                    reason=f"No meals reported for {consecutive_no_meals} consecutive days.",
                    severity="critical",
                ))

    # Build result
    if flags:
        # Take the most severe reason
        critical_flags = [f for f in flags if f.severity == "critical"]
        primary_flag = critical_flags[0] if critical_flags else flags[0]
        return SafetyCheckResult(
            is_flagged=True,
            flag_reason=primary_flag.reason,
            support_message=SUPPORT_RESOURCES,
        )

    return SafetyCheckResult(is_flagged=False)
