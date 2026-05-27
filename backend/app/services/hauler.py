from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import HaulerProfile, User
from app.schemas.user import HaulerProfileCreate


async def ensure_hauler_profile(
    db: AsyncSession, user: User, payload: HaulerProfileCreate | None = None
) -> tuple[HaulerProfile, bool]:
    """Idempotent: returns (profile, created).

    If a HaulerProfile row exists for this user, returns it without modification.
    Otherwise creates one (using payload defaults when omitted) and flips
    `user.profile.hauler_enabled = True`. Caller is responsible for committing.
    """
    existing = await db.scalar(
        select(HaulerProfile).where(HaulerProfile.user_id == user.id)
    )
    if existing is not None:
        return existing, False

    data = (payload or HaulerProfileCreate()).model_dump(exclude_unset=True)
    hauler = HaulerProfile(user_id=user.id, **data)
    db.add(hauler)
    user.profile.hauler_enabled = True
    await db.flush()
    return hauler, True
