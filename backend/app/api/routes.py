"""
API Routes — Users, Profiles, Check-ins, Recommendations, Feedback, Insights.
"""

import json
from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import (
    User, UserProfile, DailyHealthData, Recommendation,
    RecommendationAction, Feedback as FeedbackModel, HealthInsight,
    HealthDimension,
)
from app.schemas.schemas import (
    UserCreate, UserResponse,
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    DailyCheckInCreate, DailyCheckInResponse,
    RecommendationResponse, MarkCompleteRequest,
    FeedbackCreate, FeedbackResponse,
    WeeklyInsightsResponse, HealthInsightResponse,
    PriorityResult,
)
from app.services.safety_layer import check_safety
from app.services.scoring_engine import compute_baseline, score_dimensions
from app.services.priority_engine import determine_priority
from app.services.llm_service import generate_explanation
from app.services.insights_service import compute_weekly_insight

router = APIRouter()


# ==================== Users ====================

@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user (called after Supabase Auth sign-up)."""
    existing = db.query(User).filter(
        (User.supabase_uid == user_data.supabase_uid) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.")

    user = User(
        supabase_uid=user_data.supabase_uid,
        email=user_data.email,
        display_name=user_data.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ==================== Profile ====================

@router.post("/profile", response_model=UserProfileResponse, status_code=201)
def create_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create user profile (onboarding)."""
    if current_user.profile:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists.")

    profile = UserProfile(user_id=current_user.id, **profile_data.model_dump(exclude_none=True))
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    for key, val in profile_data.model_dump(exclude_none=True).items():
        setattr(current_user.profile, key, val)
    db.commit()
    db.refresh(current_user.profile)
    return current_user.profile


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    if not current_user.profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return current_user.profile


# ==================== Daily Check-in ====================

@router.post("/checkin", response_model=RecommendationResponse, status_code=201)
async def daily_checkin(
    checkin_data: DailyCheckInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit daily check-in → safety check → score → prioritise → LLM explain.
    Returns the day's recommendation.
    """
    # Check for existing check-in on this date
    existing = db.query(DailyHealthData).filter(
        DailyHealthData.user_id == current_user.id,
        DailyHealthData.check_in_date == checkin_data.check_in_date,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Check-in already exists for {checkin_data.check_in_date}.",
        )

    # Save check-in
    health_data = DailyHealthData(
        user_id=current_user.id,
        **checkin_data.model_dump(),
    )
    db.add(health_data)
    db.commit()
    db.refresh(health_data)

    # Get recent check-ins for baseline + safety
    recent_checkins_db = (
        db.query(DailyHealthData)
        .filter(
            DailyHealthData.user_id == current_user.id,
            DailyHealthData.check_in_date < checkin_data.check_in_date,
        )
        .order_by(DailyHealthData.check_in_date.desc())
        .limit(14)
        .all()
    )
    recent_dicts = [_checkin_to_dict(c) for c in recent_checkins_db]
    current_dict = checkin_data.model_dump()

    # ---- SAFETY LAYER (runs FIRST, cannot be overridden) ----
    safety_result = check_safety(current_dict, recent_dicts)

    if safety_result.is_flagged:
        # Create a safety-flagged recommendation — suppresses normal priority logic
        rec = Recommendation(
            user_id=current_user.id,
            daily_health_data_id=health_data.id,
            recommendation_date=checkin_data.check_in_date,
            priority_dimension=HealthDimension.RECOVERY,
            priority_reason=safety_result.flag_reason or "Safety concern detected.",
            safety_flagged=True,
            safety_message=safety_result.support_message,
            llm_explanation=None,  # No LLM explanation for safety-flagged responses
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    # ---- SCORING ENGINE ----
    profile_dict = None
    if current_user.profile:
        profile_dict = {
            "typical_sleep_hours": current_user.profile.typical_sleep_hours,
            "activity_level": current_user.profile.activity_level,
        }

    baseline = compute_baseline(recent_dicts)
    dimension_scores = score_dimensions(current_dict, baseline, profile_dict)

    # ---- PRIORITY ENGINE ----
    recent_recs = (
        db.query(Recommendation)
        .filter(
            Recommendation.user_id == current_user.id,
            Recommendation.safety_flagged == False,
        )
        .order_by(Recommendation.recommendation_date.desc())
        .limit(5)
        .all()
    )
    recent_priorities = [r.priority_dimension.value for r in recent_recs]

    priority_result = determine_priority(dimension_scores, recent_priorities)

    # ---- LLM EXPLANATION ----
    llm_explanation = await generate_explanation(priority_result)

    # ---- SAVE RECOMMENDATION ----
    score_details_json = json.dumps([
        {
            "dimension": s.dimension.value,
            "current_value": s.current_value,
            "baseline_value": s.baseline_value,
            "description": s.deviation_description,
        }
        for s in dimension_scores
    ])

    rec = Recommendation(
        user_id=current_user.id,
        daily_health_data_id=health_data.id,
        recommendation_date=checkin_data.check_in_date,
        priority_dimension=HealthDimension(priority_result.priority_dimension.value),
        priority_reason=priority_result.priority_reason,
        score_details=score_details_json,
        llm_explanation=llm_explanation,
        safety_flagged=False,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Save actions
    for i, action_text in enumerate(priority_result.suggested_actions):
        action = RecommendationAction(
            recommendation_id=rec.id,
            action_text=action_text,
            order=i + 1,
        )
        db.add(action)
    db.commit()
    db.refresh(rec)

    return rec


@router.get("/checkins", response_model=List[DailyCheckInResponse])
def get_checkins(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(30, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's check-in history."""
    query = db.query(DailyHealthData).filter(DailyHealthData.user_id == current_user.id)
    if start_date:
        query = query.filter(DailyHealthData.check_in_date >= start_date)
    if end_date:
        query = query.filter(DailyHealthData.check_in_date <= end_date)
    return query.order_by(DailyHealthData.check_in_date.desc()).limit(limit).all()


# ==================== Recommendations ====================

@router.get("/recommendations/today", response_model=Optional[RecommendationResponse])
def get_today_recommendation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get today's recommendation if it exists."""
    today = date.today()
    rec = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id,
        Recommendation.recommendation_date == today,
    ).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No recommendation for today. Complete your check-in first.")
    return rec


@router.get("/recommendations", response_model=List[RecommendationResponse])
def get_recommendations(
    limit: int = Query(14, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recommendation history."""
    return (
        db.query(Recommendation)
        .filter(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.recommendation_date.desc())
        .limit(limit)
        .all()
    )


@router.post("/recommendations/{rec_id}/complete", response_model=RecommendationResponse)
def mark_complete(
    rec_id: UUID,
    body: Optional[MarkCompleteRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a recommendation or specific actions as completed."""
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.user_id == current_user.id,
    ).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")

    if body and body.action_ids:
        # Mark specific actions
        for action in rec.actions:
            if action.id in body.action_ids:
                action.is_completed = True
    else:
        # Mark all actions + overall
        for action in rec.actions:
            action.is_completed = True

    rec.is_completed = True
    rec.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec


# ==================== Feedback ====================

@router.post("/recommendations/{rec_id}/feedback", response_model=FeedbackResponse, status_code=201)
def submit_feedback(
    rec_id: UUID,
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit feedback on a recommendation (did you complete it? did it help?)."""
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.user_id == current_user.id,
    ).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")

    existing_feedback = db.query(FeedbackModel).filter(
        FeedbackModel.recommendation_id == rec_id,
    ).first()
    if existing_feedback:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Feedback already submitted.")

    feedback = FeedbackModel(
        recommendation_id=rec_id,
        user_id=current_user.id,
        **feedback_data.model_dump(exclude_none=True),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


# ==================== Weekly Insights ====================

@router.get("/insights/weekly", response_model=WeeklyInsightsResponse)
def get_weekly_insights(
    week_start: Optional[date] = Query(None, description="Monday of the target week (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get weekly insights. Returns 'not enough data' if <7 days of check-ins.
    """
    return compute_weekly_insight(db, current_user.id, week_start)


@router.get("/insights/history", response_model=List[HealthInsightResponse])
def get_insight_history(
    limit: int = Query(8, le=52),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get historical weekly insights."""
    return (
        db.query(HealthInsight)
        .filter(HealthInsight.user_id == current_user.id)
        .order_by(HealthInsight.week_start.desc())
        .limit(limit)
        .all()
    )


# ==================== Health Summary ====================

@router.get("/health/today")
def get_today_health_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get today's health data + recommendation in one call (for the Today screen)."""
    today = date.today()

    checkin = db.query(DailyHealthData).filter(
        DailyHealthData.user_id == current_user.id,
        DailyHealthData.check_in_date == today,
    ).first()

    rec = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id,
        Recommendation.recommendation_date == today,
    ).first()

    return {
        "has_checked_in": checkin is not None,
        "check_in": DailyCheckInResponse.model_validate(checkin) if checkin else None,
        "recommendation": RecommendationResponse.model_validate(rec) if rec else None,
    }


# ==================== Helpers ====================

def _checkin_to_dict(checkin: DailyHealthData) -> dict:
    return {
        "sleep_hours": checkin.sleep_hours,
        "sleep_quality": checkin.sleep_quality,
        "activity_minutes": checkin.activity_minutes,
        "steps_estimate": checkin.steps_estimate,
        "water_glasses": checkin.water_glasses,
        "stress_level": checkin.stress_level,
        "meals_eaten": checkin.meals_eaten,
        "meal_quality": checkin.meal_quality,
        "energy_level": checkin.energy_level,
        "mood": checkin.mood,
        "notes": checkin.notes,
    }
