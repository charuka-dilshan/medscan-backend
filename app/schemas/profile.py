from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    conditions: Optional[str] = None
    allergies: Optional[str] = None


class ProfileResponse(ProfileCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True