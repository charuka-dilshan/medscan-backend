# File: app/dashboard/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_id
from app.database import get_db
from app.models.profile import HealthProfile
from app.models.reminder import Reminder
from app.models.scan_log import ScanLog
from app.models.user import User
from app.schemas.dashboard import DashboardResponse


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/",
    response_model=DashboardResponse,
)
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Return the authenticated user's profile,
    recent scans, and active reminders.
    """

    # 1. Get user details
    user_result = db.execute(
        select(User).where(
            User.id == current_user_id
        )
    )

    user = user_result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # 2. Get health profile
    profile_result = db.execute(
        select(HealthProfile).where(
            HealthProfile.user_id == current_user_id
        )
    )

    profile = profile_result.scalars().first()

    # 3. Get latest five scans
    scans_result = db.execute(
        select(ScanLog)
        .where(
            ScanLog.user_id == current_user_id
        )
        .order_by(
            desc(ScanLog.created_at)
        )
        .limit(5)
    )

    recent_scans = scans_result.scalars().all()

    # 4. Get active reminders
    reminders_result = db.execute(
        select(Reminder).where(
            Reminder.user_id == current_user_id,
            Reminder.active.is_(True),
        )
    )

    upcoming_reminders = reminders_result.scalars().all()

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "profile": {
            "date_of_birth": profile.date_of_birth,
            "gender": profile.gender,
            "height": profile.height,
            "weight": profile.weight,
            "bmi": profile.bmi,
            "conditions": profile.conditions,
            "allergies": profile.allergies,
        } if profile else None,
        "recent_scans": [
            {
                "id": scan.id,
                "scan_type": scan.scan_type,
                "status": scan.status,
                "confidence": scan.confidence,
                "created_at": scan.created_at,
            }
            for scan in recent_scans
        ],
        "upcoming_reminders": [
            {
                "id": reminder.id,
                "title": reminder.title,
                "medicine_name": reminder.medicine_name,
                "time": reminder.time,
                "frequency": reminder.frequency,
            }
            for reminder in upcoming_reminders
        ],
    }