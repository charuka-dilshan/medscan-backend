from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_id
from app.database import get_db
from app.models.profile import HealthProfile
from app.schemas.profile import ProfileCreate, ProfileResponse


router = APIRouter(
    prefix="/profile",
    tags=["Health Profile"],
)


@router.post(
    "/",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Create a health profile for the authenticated user.
    """

    result = db.execute(
        select(HealthProfile).where(
            HealthProfile.user_id == current_user_id
        )
    )

    existing_profile = result.scalars().first()

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PUT to update.",
        )

    new_profile = HealthProfile(
        user_id=current_user_id,
        **profile_data.model_dump(),
    )

    try:
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

    except Exception:
        db.rollback()
        raise

    return new_profile


@router.get(
    "/",
    response_model=ProfileResponse,
)
def get_profile(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Return the authenticated user's health profile.
    """

    result = db.execute(
        select(HealthProfile).where(
            HealthProfile.user_id == current_user_id
        )
    )

    profile = result.scalars().first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found.",
        )

    return profile


@router.put(
    "/",
    response_model=ProfileResponse,
)
def update_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Update the authenticated user's health profile.
    """

    result = db.execute(
        select(HealthProfile).where(
            HealthProfile.user_id == current_user_id
        )
    )

    profile = result.scalars().first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found.",
        )

    update_data = profile_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(profile, key, value)

    try:
        db.commit()
        db.refresh(profile)

    except Exception:
        db.rollback()
        raise

    return profile