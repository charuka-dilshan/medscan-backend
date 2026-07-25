from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(
    "user_id",
    Integer,
    primary_key=True,
    index=True,
)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships (අනෙකුත් Tables එක්ක තියන සම්බන්ධතාවය)
    profile = relationship("HealthProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    scan_logs = relationship(
    "ScanLog",
    back_populates="user",
)