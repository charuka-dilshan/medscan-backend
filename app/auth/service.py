# 📂 File Path: app/auth/service.py
import os
from datetime import datetime, timedelta
import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

# Secrets (.env එකෙන් කියවයි, නැතහොත් fallback අගයක් ගනී)
JWT_SECRET = os.getenv("JWT_SECRET", "medscan-ai-hackathon-secret-key-2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # ටෝකන් එක දින 1ක් (මිනිට්තු 1440) වලංගු වේ

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """පරිශීලකයාගේ මුරපදය ආරක්ෂිතව Hash කිරීම"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """ඇතුලත් කල මුරපදය සහ Database එකේ ඇති Hash එක සැසඳීම"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_access_token(data: dict) -> str:
        """JWT Token එකක් සෑදීම"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)