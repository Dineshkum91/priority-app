"""
SQLAlchemy models for the Priority app.

Models:
- User: auth identity (synced from Supabase Auth)
- UserProfile: onboarding data + personal baselines
- DailyHealthData: daily check-in inputs
- Recommendation: one per day, the prioritised output
- RecommendationAction: 2-3 actions per recommendation
- Feedback: user feedback on recommendations
- HealthInsight: weekly computed insights (only when ≥7 days data)
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, Date, DateTime,
    ForeignKey, Enum as SAEnum, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


# ---------- Enums ----------

class HealthDimension(str, enum.Enum):
    SLEEP = "sleep"
    ACTIVITY = "activity"
    HYDRATION = "hydration"
    STRESS = "stress"
    NUTRITION = "nutrition"
    RECOVERY = "recovery"


class FeedbackResponse(str, enum.Enum):
    YES = "yes"
    NO = "no"
    UNSURE = "unsure"


# ---------- Models ----------

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_uid = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    daily_health_data = relationship("DailyHealthData", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    health_insights = relationship("HealthInsight", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    """Lightweight onboarding data — no medical questionnaire."""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    age = Column(Integer, nullable=True)
    # Goals: freeform text, e.g. "sleep better, stress less"
    goals = Column(Text, nullable=True)
    typical_sleep_hours = Column(Float, nullable=True)
    activity_level = Column(String(50), nullable=True)  # sedentary, light, moderate, active
    schedule_type = Column(String(50), nullable=True)  # regular, irregular, night_owl
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

    __table_args__ = (
        CheckConstraint("age >= 13 AND age <= 120", name="check_age_range"),
    )


class DailyHealthData(Base):
    """Daily check-in: 5-6 inputs, ≤30 seconds."""
    __tablename__ = "daily_health_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    check_in_date = Column(Date, nullable=False, index=True)

    # Sleep
    sleep_hours = Column(Float, nullable=True)  # hours slept last night
    sleep_quality = Column(Integer, nullable=True)  # 1-5 self-reported

    # Activity
    activity_minutes = Column(Integer, nullable=True)  # minutes of intentional movement
    steps_estimate = Column(Integer, nullable=True)  # rough estimate or from phone

    # Hydration
    water_glasses = Column(Integer, nullable=True)  # glasses of water (approx 250ml each)

    # Stress
    stress_level = Column(Integer, nullable=True)  # 1-5, self-reported

    # Nutrition
    meals_eaten = Column(Integer, nullable=True)  # number of meals
    meal_quality = Column(Integer, nullable=True)  # 1-5 subjective

    # Recovery / wellbeing
    energy_level = Column(Integer, nullable=True)  # 1-5
    mood = Column(Integer, nullable=True)  # 1-5

    # Free text (optional) — scanned by safety layer
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="daily_health_data")
    recommendation = relationship("Recommendation", back_populates="daily_health_data", uselist=False)

    __table_args__ = (
        UniqueConstraint("user_id", "check_in_date", name="uq_user_checkin_date"),
        CheckConstraint("sleep_hours >= 0 AND sleep_hours <= 24", name="check_sleep_range"),
        CheckConstraint("sleep_quality >= 1 AND sleep_quality <= 5", name="check_sleep_quality_range"),
        CheckConstraint("stress_level >= 1 AND stress_level <= 5", name="check_stress_range"),
        CheckConstraint("energy_level >= 1 AND energy_level <= 5", name="check_energy_range"),
        CheckConstraint("mood >= 1 AND mood <= 5", name="check_mood_range"),
        CheckConstraint("meal_quality >= 1 AND meal_quality <= 5", name="check_meal_quality_range"),
    )


class Recommendation(Base):
    """One recommendation per day per user — the hero output."""
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    daily_health_data_id = Column(
        UUID(as_uuid=True),
        ForeignKey("daily_health_data.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    recommendation_date = Column(Date, nullable=False, index=True)

    # Priority engine output
    priority_dimension = Column(SAEnum(HealthDimension), nullable=False)
    priority_reason = Column(Text, nullable=False)  # deterministic rule explanation
    score_details = Column(Text, nullable=True)  # JSON string of dimension scores for transparency

    # LLM-generated explanation (explanation only, not the decision)
    llm_explanation = Column(Text, nullable=True)

    # Safety flag
    safety_flagged = Column(Boolean, default=False, nullable=False)
    safety_message = Column(Text, nullable=True)

    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="recommendations")
    daily_health_data = relationship("DailyHealthData", back_populates="recommendation")
    actions = relationship("RecommendationAction", back_populates="recommendation", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="recommendation", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "recommendation_date", name="uq_user_rec_date"),
    )


class RecommendationAction(Base):
    """2-3 concrete micro-actions for a recommendation."""
    __tablename__ = "recommendation_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_text = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    recommendation = relationship("Recommendation", back_populates="actions")


class Feedback(Base):
    """Simple feedback: did you do it? did it help?"""
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    did_complete = Column(SAEnum(FeedbackResponse), nullable=True)
    did_help = Column(SAEnum(FeedbackResponse), nullable=True)
    comment = Column(Text, nullable=True)  # optional freeform

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recommendation = relationship("Recommendation", back_populates="feedback")


class HealthInsight(Base):
    """Weekly insights — only generated when ≥7 days of data exist."""
    __tablename__ = "health_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)

    # Aggregated averages for the week
    avg_sleep_hours = Column(Float, nullable=True)
    avg_activity_minutes = Column(Float, nullable=True)
    avg_water_glasses = Column(Float, nullable=True)
    avg_stress_level = Column(Float, nullable=True)
    avg_meals_eaten = Column(Float, nullable=True)
    avg_energy_level = Column(Float, nullable=True)
    avg_mood = Column(Float, nullable=True)

    # Pattern observations (only if data supports them)
    patterns = Column(Text, nullable=True)  # JSON list of observed pattern strings
    days_with_data = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="health_insights")

    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_user_week"),
    )
