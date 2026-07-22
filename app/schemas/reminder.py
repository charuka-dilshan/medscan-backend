from pydantic import BaseModel
from datetime import datetime

class ReminderCreate(BaseModel):
    title: str               # උදා: "Morning Medicine"
    medicine_name: str       # උදා: "Paracetamol"
    time: str                # උදා: "08:00 AM"
    frequency: str           # උදා: "Daily"

class ReminderResponse(ReminderCreate):
    id: int
    user_id: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True