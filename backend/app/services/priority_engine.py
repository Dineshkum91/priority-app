"""
Priority Engine — deterministic rules that select the ONE top priority.

Compares current state vs. rolling personal baseline + consistency.
Outputs ONE top priority, a reason, and 2-3 suggested actions.
Not ML, not LLM — pure deterministic rules.
"""

from typing import List, Optional, Dict
from app.schemas.schemas import (
    DimensionScore, HealthDimensionEnum, PriorityResult,
)

# ---------- Action templates per dimension ----------

ACTION_TEMPLATES: Dict[HealthDimensionEnum, List[str]] = {
    HealthDimensionEnum.SLEEP: [
        "Set a hard stop for screens 30 minutes before your target bedtime tonight.",
        "Try to go to bed within 30 minutes of the same time as last night.",
        "If you can, fit in a 20-minute nap this afternoon (before 3 PM to avoid disrupting tonight's sleep).",
    ],
    HealthDimensionEnum.ACTIVITY: [
        "Take a 15-minute walk between classes or during a break.",
        "Do a quick 10-minute stretch or bodyweight routine (no equipment needed).",
        "Walk or bike instead of driving for your next short trip today.",
    ],
    HealthDimensionEnum.HYDRATION: [
        "Fill a water bottle and keep it with you for the rest of the day.",
        "Drink a full glass of water with your next meal.",
        "Set a reminder to drink water every 2 hours.",
    ],
    HealthDimensionEnum.STRESS: [
        "Take a 5-minute breathing break: breathe in for 4 counts, hold for 4, out for 6.",
        "Write down the one thing stressing you most and one small step you could take on it.",
        "Step outside for 10 minutes — even brief time outdoors can help reset.",
    ],
    HealthDimensionEnum.NUTRITION: [
        "Eat a full meal within the next 2 hours — something with protein and a vegetable.",
        "Prepare a simple snack to have on hand (fruit, nuts, a sandwich) so you don't skip eating.",
        "If you skipped breakfast, prioritise lunch — even something small is better than nothing.",
    ],
    HealthDimensionEnum.RECOVERY: [
        "Give yourself 20 minutes of something genuinely enjoyable today — not scrolling, something that recharges you.",
        "If you're feeling drained, it's okay to say no to one non-essential commitment today.",
        "Try going to bed 30 minutes earlier tonight to help your body recover.",
    ],
    HealthDimensionEnum.SCREEN_TIME: [
        "Set your phone to grayscale mode for the rest of the day — it makes scrolling far less compelling.",
        "Pick one app that eats the most time and log out of it until tomorrow morning.",
        "Charge your phone outside the bedroom tonight and read a few pages of a book instead.",
        "Do one activity tonight (walk, shower, chores) with your phone in another room.",
    ],
    HealthDimensionEnum.CAFFEINE: [
        "Make your next drink water or decaf — keep total caffeine today within your limit.",
        "No caffeine after 2 PM today so it doesn't interfere with tonight's sleep.",
        "Swap one coffee for a 10-minute walk — the alertness boost lasts longer.",
    ],
}


def _compute_urgency(score: DimensionScore) -> float:
    """
    Compute an internal urgency value for a dimension.
    Higher = more urgent = more likely to be the top priority.

    This is an internal ranking mechanism. It is NOT exposed to users
    as a "score" or "percentage."
    """
    current = score.current_value
    baseline = score.baseline_value
    dimension = score.dimension

    if current is None:
        return 0.0  # can't prioritise what we don't have data for

    # Dimension-specific urgency logic
    if dimension == HealthDimensionEnum.SLEEP:
        if current <= 2.0:
            return 10.0  # extreme deprivation
        if current <= 4.0:
            return 7.0
        if baseline and current < baseline * 0.75:
            return 6.0
        if baseline and current < baseline * 0.9:
            return 3.0
        return 1.0

    elif dimension == HealthDimensionEnum.ACTIVITY:
        if current == 0:
            return 5.0
        if current < 15:
            return 4.0
        if baseline and current < baseline * 0.5:
            return 3.5
        return 1.0

    elif dimension == HealthDimensionEnum.HYDRATION:
        if current <= 1:
            return 5.5
        if current <= 3:
            return 4.0
        if baseline and current < baseline * 0.6:
            return 3.0
        return 1.0

    elif dimension == HealthDimensionEnum.STRESS:
        # Stress is inverted: higher value = worse
        if current >= 5:
            return 6.5
        if current >= 4:
            return 4.5
        if baseline and current > baseline * 1.4:
            return 3.5
        return 1.0

    elif dimension == HealthDimensionEnum.NUTRITION:
        if current == 0:
            return 6.0
        if current <= 1:
            return 4.5
        if baseline and current < baseline * 0.6:
            return 3.0
        return 1.0

    elif dimension == HealthDimensionEnum.RECOVERY:
        # Recovery is composite energy+mood, 1-5 scale
        if current <= 1.5:
            return 5.5
        if current <= 2.5:
            return 4.0
        if baseline and current < baseline * 0.7:
            return 3.0
        return 1.0

    elif dimension == HealthDimensionEnum.SCREEN_TIME:
        # Higher = worse (inverted dimension)
        if current > 12.0:
            return 6.0
        if current > 9.0:
            return 4.5
        if baseline and current > baseline * 1.4:
            return 3.5
        if baseline and current > baseline * 1.2:
            return 2.0
        return 1.0

    elif dimension == HealthDimensionEnum.CAFFEINE:
        # Higher = worse (inverted dimension)
        if current >= 6:
            return 5.0
        if current >= 4:
            return 3.5
        if baseline and current > baseline * 1.5:
            return 2.5
        return 1.0

    return 1.0


def determine_priority(
    dimension_scores: List[DimensionScore],
    recent_priorities: Optional[List[str]] = None,
) -> PriorityResult:
    """
    Determine the ONE top priority from scored dimensions.

    Args:
        dimension_scores: scored dimensions from scoring_engine
        recent_priorities: list of the last N priority dimension names (newest first),
                           used for the diminishing-returns modifier.

    Returns:
        PriorityResult with the top priority, reason, and suggested actions.
    """
    if not dimension_scores:
        # Fallback if somehow no scores
        return PriorityResult(
            priority_dimension=HealthDimensionEnum.RECOVERY,
            priority_reason="Not enough data to determine a specific priority today. Focus on rest and recovery.",
            dimension_scores=[],
            suggested_actions=ACTION_TEMPLATES[HealthDimensionEnum.RECOVERY][:2],
        )

    # Score each dimension
    urgency_map = {}
    for score in dimension_scores:
        urgency = _compute_urgency(score)
        urgency_map[score.dimension] = urgency

    # Diminishing returns: if same dimension has been top for 3+ consecutive days,
    # reduce its urgency slightly to allow rotation
    if recent_priorities and len(recent_priorities) >= 3:
        last_three = recent_priorities[:3]
        if len(set(last_three)) == 1:
            repeated_dim = HealthDimensionEnum(last_three[0])
            if repeated_dim in urgency_map:
                urgency_map[repeated_dim] *= 0.7  # 30% reduction

    # Sort by urgency (descending)
    sorted_dims = sorted(urgency_map.items(), key=lambda x: x[1], reverse=True)
    top_dim = sorted_dims[0][0]
    top_urgency = sorted_dims[0][1]

    # Find the corresponding score for the reason
    top_score = next(s for s in dimension_scores if s.dimension == top_dim)

    # Build reason
    if top_urgency <= 1.0:
        reason = (
            "All your health dimensions look fairly balanced today. "
            f"We're highlighting {top_dim.value} as a small area of focus."
        )
    else:
        reason = top_score.deviation_description

    # Select 2-3 actions
    actions = ACTION_TEMPLATES.get(top_dim, [])[:3]

    return PriorityResult(
        priority_dimension=top_dim,
        priority_reason=reason,
        dimension_scores=dimension_scores,
        suggested_actions=actions,
    )
