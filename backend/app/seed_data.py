"""
Seed script — populates the database with multi-day mock data for one user.
This makes Today's Priority and Weekly Insights demoable end-to-end.

Usage:
    cd priority-app/backend
    python -m app.seed_data
"""

import uuid
import json
import random
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.models.models import (
    User, UserProfile, DailyHealthData, Recommendation,
    RecommendationAction, Feedback, HealthInsight, HealthDimension, FeedbackResponse,
)
from app.services.safety_layer import check_safety
from app.services.scoring_engine import compute_baseline, score_dimensions
from app.services.priority_engine import determine_priority


def seed():
    """Create tables and seed with 14 days of mock data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Clean existing seed data
        existing_user = db.query(User).filter(User.email == "priya@example.edu").first()
        if existing_user:
            print("Seed data already exists. Clearing and re-seeding...")
            db.delete(existing_user)
            db.commit()

        # ---- Create demo user (Priya persona) ----
        user = User(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            supabase_uid="demo-priya-001",
            email="priya@example.edu",
            display_name="Priya",
        )
        db.add(user)
        db.commit()

        profile = UserProfile(
            user_id=user.id,
            age=20,
            goals="Sleep better, manage stress during exam season",
            typical_sleep_hours=7.0,
            activity_level="light",
            schedule_type="irregular",
        )
        db.add(profile)
        db.commit()

        # ---- Generate 14 days of check-in data ----
        today = date.today()
        start_date = today - timedelta(days=13)

        # Simulate realistic college-student patterns
        daily_data = [
            # Day 1-3: decent baseline
            {"sleep_hours": 7.0, "sleep_quality": 3, "activity_minutes": 25, "water_glasses": 6,
             "stress_level": 2, "meals_eaten": 3, "meal_quality": 3, "energy_level": 3, "mood": 4,
             "steps_estimate": 5000, "notes": "Good start to the week"},
            {"sleep_hours": 6.5, "sleep_quality": 3, "activity_minutes": 30, "water_glasses": 7,
             "stress_level": 2, "meals_eaten": 3, "meal_quality": 3, "energy_level": 4, "mood": 4,
             "steps_estimate": 6000, "notes": None},
            {"sleep_hours": 7.5, "sleep_quality": 4, "activity_minutes": 20, "water_glasses": 5,
             "stress_level": 3, "meals_eaten": 2, "meal_quality": 3, "energy_level": 3, "mood": 3,
             "steps_estimate": 4500, "notes": "Busy day"},
            # Day 4-6: stress ramps up (midterms)
            {"sleep_hours": 5.5, "sleep_quality": 2, "activity_minutes": 10, "water_glasses": 4,
             "stress_level": 4, "meals_eaten": 2, "meal_quality": 2, "energy_level": 2, "mood": 3,
             "steps_estimate": 3000, "notes": "Midterm studying all night"},
            {"sleep_hours": 4.0, "sleep_quality": 2, "activity_minutes": 5, "water_glasses": 3,
             "stress_level": 5, "meals_eaten": 1, "meal_quality": 2, "energy_level": 2, "mood": 2,
             "steps_estimate": 2000, "notes": "Barely slept, exam tomorrow"},
            {"sleep_hours": 4.5, "sleep_quality": 1, "activity_minutes": 0, "water_glasses": 3,
             "stress_level": 5, "meals_eaten": 2, "meal_quality": 1, "energy_level": 1, "mood": 2,
             "steps_estimate": 1500, "notes": "Exhausted after exam"},
            # Day 7-9: partial recovery
            {"sleep_hours": 9.0, "sleep_quality": 4, "activity_minutes": 15, "water_glasses": 5,
             "stress_level": 3, "meals_eaten": 3, "meal_quality": 3, "energy_level": 3, "mood": 3,
             "steps_estimate": 4000, "notes": "Crashed and slept in"},
            {"sleep_hours": 7.5, "sleep_quality": 3, "activity_minutes": 30, "water_glasses": 6,
             "stress_level": 3, "meals_eaten": 3, "meal_quality": 4, "energy_level": 3, "mood": 4,
             "steps_estimate": 5500, "notes": "Feeling a bit better"},
            {"sleep_hours": 7.0, "sleep_quality": 3, "activity_minutes": 20, "water_glasses": 5,
             "stress_level": 3, "meals_eaten": 2, "meal_quality": 3, "energy_level": 3, "mood": 3,
             "steps_estimate": 4000, "notes": None},
            # Day 10-12: another dip (project deadline)
            {"sleep_hours": 5.0, "sleep_quality": 2, "activity_minutes": 0, "water_glasses": 3,
             "stress_level": 4, "meals_eaten": 2, "meal_quality": 2, "energy_level": 2, "mood": 2,
             "steps_estimate": 2500, "notes": "Group project deadline coming up"},
            {"sleep_hours": 5.5, "sleep_quality": 2, "activity_minutes": 10, "water_glasses": 4,
             "stress_level": 4, "meals_eaten": 2, "meal_quality": 2, "energy_level": 2, "mood": 3,
             "steps_estimate": 3000, "notes": "Late night working on project"},
            {"sleep_hours": 6.0, "sleep_quality": 3, "activity_minutes": 15, "water_glasses": 5,
             "stress_level": 3, "meals_eaten": 3, "meal_quality": 3, "energy_level": 3, "mood": 3,
             "steps_estimate": 4000, "notes": "Submitted the project, relieved"},
            # Day 13-14: current days
            {"sleep_hours": 7.0, "sleep_quality": 3, "activity_minutes": 25, "water_glasses": 6,
             "stress_level": 2, "meals_eaten": 3, "meal_quality": 3, "energy_level": 3, "mood": 4,
             "steps_estimate": 5000, "notes": "Catching up on rest"},
            {"sleep_hours": 6.0, "sleep_quality": 3, "activity_minutes": 10, "water_glasses": 4,
             "stress_level": 3, "meals_eaten": 2, "meal_quality": 2, "energy_level": 3, "mood": 3,
             "steps_estimate": 3500, "notes": "Normal day, a bit tired"},
        ]

        all_checkins = []
        all_priorities = []

        for i, data in enumerate(daily_data):
            checkin_date = start_date + timedelta(days=i)
            health_data = DailyHealthData(
                user_id=user.id,
                check_in_date=checkin_date,
                **data,
            )
            db.add(health_data)
            db.commit()
            db.refresh(health_data)
            all_checkins.append(health_data)

            # Run the scoring + priority pipeline for each day
            recent_dicts = [
                _checkin_to_dict(c) for c in reversed(all_checkins[:-1])
            ][-7:]  # last 7 days before today
            recent_dicts.reverse()  # newest first

            current_dict = data.copy()
            del current_dict["notes"]
            current_dict["notes"] = data.get("notes")

            # Safety check
            safety = check_safety(current_dict, recent_dicts)

            if safety.is_flagged:
                rec = Recommendation(
                    user_id=user.id,
                    daily_health_data_id=health_data.id,
                    recommendation_date=checkin_date,
                    priority_dimension=HealthDimension.RECOVERY,
                    priority_reason=safety.flag_reason,
                    safety_flagged=True,
                    safety_message=safety.support_message,
                )
                db.add(rec)
                all_priorities.append(HealthDimension.RECOVERY.value)
            else:
                baseline = compute_baseline(recent_dicts)
                profile_dict = {
                    "typical_sleep_hours": profile.typical_sleep_hours,
                    "activity_level": profile.activity_level,
                }
                scores = score_dimensions(current_dict, baseline, profile_dict)
                priority = determine_priority(scores, all_priorities[-5:])

                score_details = json.dumps([
                    {
                        "dimension": s.dimension.value,
                        "current_value": s.current_value,
                        "baseline_value": s.baseline_value,
                        "description": s.deviation_description,
                    }
                    for s in scores
                ])

                rec = Recommendation(
                    user_id=user.id,
                    daily_health_data_id=health_data.id,
                    recommendation_date=checkin_date,
                    priority_dimension=HealthDimension(priority.priority_dimension.value),
                    priority_reason=priority.priority_reason,
                    score_details=score_details,
                    llm_explanation=f"Today, your top priority is {priority.priority_dimension.value}. {priority.priority_reason}",
                    safety_flagged=False,
                )
                db.add(rec)
                db.commit()
                db.refresh(rec)

                for j, action in enumerate(priority.suggested_actions):
                    act = RecommendationAction(
                        recommendation_id=rec.id,
                        action_text=action,
                        order=j + 1,
                        is_completed=random.random() > 0.5 if i < 12 else False,
                    )
                    db.add(act)

                all_priorities.append(priority.priority_dimension.value)

                # Add some feedback for older days
                if i < 10:
                    feedback = Feedback(
                        recommendation_id=rec.id,
                        user_id=user.id,
                        did_complete=random.choice([FeedbackResponse.YES, FeedbackResponse.YES, FeedbackResponse.NO]),
                        did_help=random.choice([FeedbackResponse.YES, FeedbackResponse.UNSURE, FeedbackResponse.NO]),
                    )
                    db.add(feedback)

        db.commit()

        print(f"\n✅ Seed data created successfully!")
        print(f"   User: Priya ({user.email})")
        print(f"   User ID: {user.id}")
        print(f"   Check-ins: {len(all_checkins)} days ({start_date} to {today})")
        print(f"   Dev auth token: Bearer dev:{user.id}")
        print(f"\n   Try: curl -H 'Authorization: Bearer dev:{user.id}' http://localhost:8000/api/v1/health/today")

    finally:
        db.close()


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


if __name__ == "__main__":
    seed()
