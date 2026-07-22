from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.profile import HealthProfile
from app.models.reminder import Reminder
from app.models.scan_log import ScanLog  # AI ඩිවෙලොපර් පාවිච්චි කරන ටේබල් එක
from app.schemas.dashboard import DashboardResponse
from app.auth.dependencies import get_current_user_id

router = APIRouter()

@router.get("/", response_model=DashboardResponse)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """යූසර්ගේ මුළු ප්‍රොෆයිල්, ස්කෑන් සහ රිමේන්ඩර්ස් සාරාංශය එකම තැනකින් ලබා ගැනීම"""
    
    # 1. යූසර්ගේ විස්තර ලබා ගැනීම
    user_result = await db.execute(select(User).where(User.id == current_user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # 2. හෙල්ත් ප්‍රොෆයිල් එක ලබා ගැනීම
    profile_result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == current_user_id))
    profile = profile_result.scalars().first()

    # 3. මෑතකදීම සිදුකල ස්කෑන් 5 ලබා ගැනීම (Latest 5 Scans)
    scans_result = await db.execute(
        select(ScanLog)
        .where(ScanLog.user_id == current_user_id)
        .order_by(desc(ScanLog.created_at))
        .limit(5)
    )
    recent_scans = scans_result.scalars().all()

    # 4. රිමේන්ඩර්ස් ලැයිස්තුව ලබා ගැනීම
    reminders_result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == current_user_id, Reminder.active == True)
    )
    upcoming_reminders = reminders_result.scalars().all()

    # දත්ත එකතු කර Response එක සකස් කිරීම
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        "profile": {
            "age": profile.age,
            "gender": profile.gender,
            "bmi": profile.bmi,
            "conditions": profile.conditions
        } if profile else None,
        "recent_scans": [
            {
                "id": s.id,
                "scan_type": s.scan_type,
                "status": s.status,
                "confidence": s.confidence,
                "created_at": s.created_at
            } for s in recent_scans
        ],
        "upcoming_reminders": [
            {
                "id": r.id,
                "title": r.title,
                "medicine_name": r.medicine_name,
                "time": r.time,
                "frequency": r.frequency
            } for r in upcoming_reminders
        ]
    }