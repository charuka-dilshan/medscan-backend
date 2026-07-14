from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from database import Base
import datetime

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)              # "success" හෝ "safety_block" වගේ තත්ත්වයන් සේව් කරන්න
    raw_text = Column(String)            # OCR එකෙන් අහුවුණු raw text එක
    confidence = Column(Float)           # OCR එකේ confidence score එක
    prescription_json = Column(JSON)     # Groq AI එකෙන් ලැබෙන structured JSON data එක සේව් කරන Column එක 🚀
    created_at = Column(DateTime, default=datetime.datetime.utcnow)