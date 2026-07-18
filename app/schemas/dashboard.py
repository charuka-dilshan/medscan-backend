from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Dashboard එකේ පෙන්වන්න ඕන සරල කරපු දත්ත ආකෘති
class UserSummary(BaseModel):
    id: int
    name: str
    email: str

class ProfileSummary(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    bmi: Optional[float] = None
    conditions: Optional[str] = None

class ScanLogSummary(BaseModel):
    id: int
    scan_type: str
    status: str
    confidence: float
    created_at: datetime

class ReminderSummary(BaseModel):
    id: int
    title: str
    medicine_name: str
    time: str
    frequency: str

# ප්‍රධාන Dashboard Response එක
class DashboardResponse(BaseModel):
    user: UserSummary
    profile: Optional[ProfileSummary] = None
    recent_scans: List[ScanLogSummary] = []
    upcoming_reminders: List[ReminderSummary] = []