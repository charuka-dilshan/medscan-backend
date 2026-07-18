import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "medscan-ai-hackathon-secret-key-2026")
JWT_ALGORITHM = "HS256"

# Swagger UI සහ Flutter වලින් එන Authorization Header Token එක කියවීමට
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """Token එක පරීක්ෂා කර එහි අඩංගු user_id එක පිටතට ලබා දීම"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please login again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return user_id
    except jwt.PyJWTError:
        raise credentials_exception