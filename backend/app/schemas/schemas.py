"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum


# ---------- Enums ----------

class HealthDimensionEnum(str, Enum):
    SLEEP = "sleep"
    ACTIVITY = "activity"
    HYDRATION = "hydration"
    STRESS = "stress"
    NUTRITION = "nutrition"
    RECOVERY = "recovery"


class FeedbackResponseEnum(str, Enum):
    YES = "yes"
    NO = "no"
    UNSURE = "unsure"


# ---------- User ----------

class UserCreate(BaseModel):
    supabase_uid: str
    email: str
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    supabase_uid: str
    email: str
    display_name: Optional[str]
    created_at: datetime


# ---------- UserProfile ----------

class UserProfileCreate(BaseModel):
    age: Optional[int] = Field(None, ge=13, le=120)
    goals: Optional[str] = None
    typical_sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    activity_level: Optional[str] = Field(None, pattern=r"^(sedentary|light|moderate|active)$")
    schedule_type: Optional[str] = Field(None, pattern=r"^(regular|irregular|night_owl)$")


class UserProfileUpdate(BaseModel):
    age: Optional[int] = Field(None, ge=13, le=120)
    goals: Optional[str] = None
    typical_sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    activity_level: Optional[str] = Field(None, pattern=r"^(sedentary|light|moderate|active)$")
    schedule_type: Optional[str] = Field(None, pattern=r"^(regular|irregular|night_owl)$")


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    age: Optional[int]
    goals: Optional[str]
    typical_sleep_hours: Optional[float]
    activity_level: Optional[str]
    schedule_type: Optional[str]
    created_at: datetime


# ---------- DailyHealthData (Check-in) ----------

class DailyCheckInCreate(BaseModel):
    """Daily check-in input — all fields optional to minimise friction."""
    check_in_date: date
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_quality: Optional[int] = Field(None, ge=1, le=5)
    activity_minutes: Optional[int] = Field(None, ge=0)
    steps_estimate: Optional[int] = Field(None, ge=0)
    water_glasses: Optional[int] = Field(None, ge=0)
    stress_level: Optional[int] = Field(None, ge=1, le=5)
    meals_eaten: Optional[int] = Field(None, ge=0, le=10)
    meal_quality: Optional[int] = Field(None, ge=1, le=5)
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    mood: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None


class DailyCheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    check_in_date: date
    sleep_hours: Optional[float]
    sleep_quality: Optional[int]
    activity_minutes: Optional[int]
    steps_estimate: Optional[int]
    water_glasses: Optional[int]
    stress_level: Optional[int]
    meals_eaten: Optional[int]
    meal_quality: Optional[int]
    energy_level: Optional[int]
    mood: Optional[int]
    notes: Optional[str]
    created_at: datetime


# ---------- Recommendation ----------

class RecommendationActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    action_text: str
    order: int
    is_completed: bool


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    recommendation_date: date
    priority_dimension: HealthDimensionEnum
    priority_reason: str
    llm_explanation: Optional[str]
    safety_flagged: bool
    safety_message: Optional[str]
    is_completed: bool
    completed_at: Optional[datetime]
    actions: List[RecommendationActionResponse] = []
    created_at: datetime


class MarkCompleteRequest(BaseModel):
    action_ids: Optional[List[UUID]] = None  # specific actions, or None for all


# ---------- Feedback ----------

class FeedbackCreate(BaseModel):
    did_complete: Optional[FeedbackResponseEnum] = None
    did_help: Optional[FeedbackResponseEnum] = None
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    recommendation_id: UUID
    did_complete: Optional[FeedbackResponseEnum]
    did_help: Optional[FeedbackResponseEnum]
    comment: Optional[str]
    created_at: datetime


# ---------- Health Insights ----------

class HealthInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    week_start: date
    week_end: date
    avg_sleep_hours: Optional[float]
    avg_activity_minutes: Optional[float]
    avg_water_glasses: Optional[float]
    avg_stress_level: Optional[float]
    avg_meals_eaten: Optional[float]
    avg_energy_level: Optional[float]
    avg_mood: Optional[float]
    patterns: Optional[str]
    days_with_data: int
    created_at: datetime


class WeeklyInsightsResponse(BaseModel):
    """Wrapper that indicates whether enough data exists."""
    has_sufficient_data: bool  # True only if ≥7 days
    message: str  # "Not enough data yet" or summary
    insight: Optional[HealthInsightResponse] = None


# ---------- Safety ----------

class SafetyCheckResult(BaseModel):
    is_flagged: bool
    flag_reason: Optional[str] = None
    support_message: Optional[str] = None


# ---------- Priority Engine Output ----------

class DimensionScore(BaseModel):
    dimension: HealthDimensionEnum
    current_value: Optional[float]
    baseline_value: Optional[float]
    deviation_description: str  # plain-language description, not a raw score


class PriorityResult(BaseModel):
    priority_dimension: HealthDimensionEnum
    priority_reason: str
    dimension_scores: List[DimensionScore]
    suggested_actions: List[str]
    safety_override: bool = False
