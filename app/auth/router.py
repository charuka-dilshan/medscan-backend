# 📂 File Path: app/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse
from app.auth.service import AuthService

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 1. Email එක පද්ධතියේ දැනටමත් තිබේදැයි බැලීම
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered."
        )
    
    # 2. Password Hash කර නව පරිශීලකයෙක් සෑදීම
    hashed_pass = AuthService.hash_password(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_pass
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # 3. ලියාපදිංචි වූ සැනින්ම Auto-Login වීමට ටෝකනයක් සාදා යැවීම
    token = AuthService.create_access_token({"user_id": new_user.id, "email": new_user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "name": new_user.name
    }

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # 1. පරිශීලකයා සොයා ගැනීම
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()
    
    # 2. මුරපදය නිවැරදිදැයි බැලීම
    if not user or not AuthService.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # 3. ටෝකනය සාදා යැවීම
    token = AuthService.create_access_token({"user_id": user.id, "email": user.email})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name
    }