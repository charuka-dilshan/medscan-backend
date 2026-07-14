from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    scan_type = Column(String, nullable=False)    # "prescription" හෝ "pill"
    ocr_text = Column(String, nullable=True)      # OCR එකෙන් අහුවුණු raw text එක
    prediction = Column(String, nullable=True)    # AI එකෙන් අඳුනගත්තු ලෙඩේ හෝ බෙහෙත
    confidence = Column(Float, nullable=False)    # AI/OCR Confidence Score එක
    status = Column(String, default="success")    # "success" හෝ "flagged_low_confidence"
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to User
    user = relationship("User", back_populates="scan_logs")