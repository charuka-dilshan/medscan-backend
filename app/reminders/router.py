from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.auth.dependencies import get_current_user_id

router = APIRouter()

@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_data: ReminderCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """නව බෙහෙත් මතක් කිරීමක් (Reminder) පද්ධතියට ඇතුලත් කිරීම"""
    new_reminder = Reminder(
        user_id=current_user_id,
        **reminder_data.model_dump()
    )
    db.add(new_reminder)
    await db.commit()
    await db.refresh(new_reminder)
    return new_reminder

@router.get("/", response_model=list[ReminderResponse])
async def get_reminders(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """ලොග් වී සිටින පරිශීලකයාගේ සියලුම සක්‍රීය රිමේන්ඩර්ස් ලැයිස්තුව ලබා ගැනීම"""
    result = await db.execute(
        select(Reminder).where(Reminder.user_id == current_user_id, Reminder.active == True)
    )
    reminders = result.scalars().all()
    return reminders

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """නිශ්චිත රිමේන්ඩර් එකක් පද්ධතියෙන් ඉවත් කිරීම (Soft Delete / Active state false කිරීම)"""
    result = await db.execute(
        select(Reminder).where(Reminder.id == id, Reminder.user_id == current_user_id)
    )
    reminder = result.scalars().first()
    
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Reminder not found or you don't have permission to delete it."
        )
    
    # හැකතන් ස්පීඩ් එකට සරලව active එක false කරමු, නැතහොත් db.delete(reminder) උනත් පුළුවන්
    reminder.active = False
    await db.commit()
    return None