from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True)  # cm හෝ meters වලින්
    weight = Column(Float, nullable=True)  # kg වලින්
    bmi = Column(Float, nullable=True)
    
    conditions = Column(String, nullable=True)  # පවතින ලෙඩ රෝග (Comma-separated text හෝ JSON string)
    allergies = Column(String, nullable=True)   # අසාත්මිකතා
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to User
    user = relationship("User", back_populates="profile")