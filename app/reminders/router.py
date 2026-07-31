from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_id
from app.database import get_db
from app.models.reminder import Reminder
from app.schemas.reminder import (
    ReminderCreate,
    ReminderResponse,
    ReminderUpdate,
)


router = APIRouter(
    prefix="/reminders",
    tags=["Reminders"],
)


@router.post(
    "/",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    reminder_data: ReminderCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Create a new medicine reminder for the authenticated user.
    """

    new_reminder = Reminder(
        user_id=current_user_id,
        **reminder_data.model_dump(),
    )

    try:
        db.add(new_reminder)
        db.commit()
        db.refresh(new_reminder)

    except Exception:
        db.rollback()
        raise

    return new_reminder


@router.get(
    "/",
    response_model=list[ReminderResponse],
)
def get_reminders(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Return all active reminders for the authenticated user.
    """

    result = db.execute(
        select(Reminder).where(
            Reminder.user_id == current_user_id,
            Reminder.active.is_(True),
        )
    )

    return result.scalars().all()


@router.put(
    "/{reminder_id}",
    response_model=ReminderResponse,
)
def update_reminder(
    reminder_id: int,
    reminder_data: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Update a reminder belonging to the authenticated user.
    """

    result = db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user_id,
        )
    )

    reminder = result.scalars().first()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found or access denied.",
        )

    update_data = reminder_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(reminder, key, value)

    try:
        db.commit()
        db.refresh(reminder)

    except Exception:
        db.rollback()
        raise

    return reminder


@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Soft-delete a reminder by setting active to False.
    """

    result = db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user_id,
        )
    )

    reminder = result.scalars().first()

    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found or access denied.",
        )

    reminder.active = False

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return None