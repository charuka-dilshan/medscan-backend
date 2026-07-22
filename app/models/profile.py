from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Fields
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    height = Column(Float, nullable=True)  # in cm/m
    weight = Column(Float, nullable=True)  # in kg
    bmi = Column(Float, nullable=True)
    
    # Health background
    conditions = Column(String, nullable=True)  # Comma-separated list or text
    allergies = Column(String, nullable=True)   # Comma-separated list or text
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to User Table
    user = relationship("User", back_populates="profile")