from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String, nullable=False)          # උදා: "Morning Medicine"
    medicine_name = Column(String, nullable=False)  # බෙහෙතේ නම
    time = Column(String, nullable=False)           # බෙහෙත් බොන්න ඕන වෙලාව (උදා: "08:00 AM")
    frequency = Column(String, nullable=False)      # දිනපතාද, සතියකට වරක්ද (Daily / Weekly)
    active = Column(Boolean, default=True)          # Reminder එක active ද නැද්ද කියා බැලීමට
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to User
    user = relationship("User", back_populates="reminders")