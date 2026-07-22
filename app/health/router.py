from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.profile import HealthProfile
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.auth.dependencies import get_current_user_id

router = APIRouter()

@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """පරිශීලකයාට නව සෞඛ්‍ය ප්‍රොෆයිලයක් සෑදීම"""
    # දැනටමත් Profile එකක් තියෙනවද කියා බැලීම
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == current_user_id))
    existing_profile = result.scalars().first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Profile already exists. Use PUT to update."
        )

    new_profile = HealthProfile(
        user_id=current_user_id,
        **profile_data.model_dump()
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

@router.get("/", response_model=ProfileResponse)
async def get_profile(
    db: AsyncSession = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """ලොග් වී සිටින පරිශීලකයාගේ සෞඛ්‍ය ප්‍රොෆයිලය ලබා ගැනීම"""
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == current_user_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health profile not found.")
    return profile

@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user_id: int = Depends(get_current_user_id)
):
    """ප්‍රොෆයිලයේ දත්ත (Age, Weight, Allergies ආදිය) යාවත්කාලීන කිරීම"""
    result = await db.execute(select(HealthProfile).where(HealthProfile.user_id == current_user_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health profile not found.")

    # එවා ඇති දත්ත පමණක් Update කිරීම
    for key, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return profile