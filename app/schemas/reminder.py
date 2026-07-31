from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    title: str
    medicine_name: str
    time: str
    frequency: str


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    medicine_name: Optional[str] = None
    time: Optional[str] = None
    frequency: Optional[str] = None
    active: Optional[bool] = None


class ReminderResponse(ReminderCreate):
    id: int
    user_id: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True