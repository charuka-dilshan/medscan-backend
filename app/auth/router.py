# 📂 File Path: app/auth/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import AuthService
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister


router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    # 1. Check whether the email is already registered
    result = db.execute(
        select(User).where(
            User.email == user_data.email
        )
    )

    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered.",
        )

    # 2. Hash the password and create the user
    hashed_password = AuthService.hash_password(
        user_data.password
    )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise

    # 3. Create an access token for automatic login
    token = AuthService.create_access_token(
        {
            "user_id": new_user.id,
            "email": new_user.email,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "name": new_user.name,
    }


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    # 1. Find the user by email
    result = db.execute(
        select(User).where(
            User.email == login_data.email
        )
    )

    user = result.scalars().first()

    # 2. Verify email and password
    if (
        not user
        or not AuthService.verify_password(
            login_data.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 3. Create the access token
    token = AuthService.create_access_token(
        {
            "user_id": user.id,
            "email": user.email,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
    }