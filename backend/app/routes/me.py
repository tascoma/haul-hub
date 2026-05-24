from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases import get_db
from app.dependencies.auth import current_user
from app.models.user import HaulerProfile, User
from app.schemas.payment import ConnectOnboardingResponse
from app.schemas.user import (
    HaulerProfileCreate,
    HaulerProfileRead,
    HaulerProfileUpdate,
    MeRead,
    UserProfileUpdate,
)
from app.services import payments

router = APIRouter()


@router.get("", response_model=MeRead)
async def read_me(user: User = Depends(current_user)) -> User:
    return user


@router.patch("", response_model=MeRead)
async def update_me(
    payload: UserProfileUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user.profile, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/enable-hauler", response_model=HaulerProfileRead, status_code=status.HTTP_201_CREATED
)
async def enable_hauler(
    payload: HaulerProfileCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> HaulerProfile:
    if user.hauler_profile is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Hauler profile already exists"
        )
    hauler = HaulerProfile(user_id=user.id, **payload.model_dump())
    db.add(hauler)
    user.profile.hauler_enabled = True
    await db.commit()
    await db.refresh(hauler)
    return hauler


@router.get("/hauler-profile", response_model=HaulerProfileRead)
async def read_hauler_profile(user: User = Depends(current_user)) -> HaulerProfile:
    if user.hauler_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hauler profile not enabled"
        )
    return user.hauler_profile


@router.post("/connect-onboarding", response_model=ConnectOnboardingResponse)
async def connect_onboarding(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectOnboardingResponse:
    if user.hauler_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enable hauler role before onboarding to Stripe Connect",
        )
    url = await payments.create_connect_onboarding_link(db, user)
    await db.commit()
    return ConnectOnboardingResponse(url=url)


@router.patch("/hauler-profile", response_model=HaulerProfileRead)
async def update_hauler_profile(
    payload: HaulerProfileUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> HaulerProfile:
    if user.hauler_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hauler profile not enabled"
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user.hauler_profile, field, value)
    await db.commit()
    await db.refresh(user.hauler_profile)
    return user.hauler_profile
