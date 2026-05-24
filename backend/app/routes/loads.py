from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases import get_db
from app.dependencies.auth import current_user
from app.models.load import Load, LoadStatus
from app.models.payment import Payment
from app.models.user import User
from app.schemas.load import (
    PRICE_RELEVANT_FIELDS,
    CancelRequest,
    LoadCreate,
    LoadRead,
    LoadUpdate,
)
from app.schemas.payment import PaymentRead
from app.services import booking
from app.services.pricing import calculate_price_cents
from app.services.storage import upload_file

router = APIRouter()

EDITABLE_STATUSES = {LoadStatus.draft, LoadStatus.posted}
CANCELLABLE_BY_SHIPPER = {LoadStatus.draft, LoadStatus.posted}


def _ensure_shipper(user: User) -> None:
    if not user.profile.shipper_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Shipper role not enabled"
        )


async def _get_owned_load(load_id: str, user: User, db: AsyncSession) -> Load:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    if load.shipper_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your load")
    return load


@router.post("", response_model=LoadRead, status_code=status.HTTP_201_CREATED)
async def create_load(
    payload: LoadCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    _ensure_shipper(user)
    if payload.pickup_window_end < payload.pickup_window_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="pickup_window_end must be >= pickup_window_start",
        )

    price = calculate_price_cents(
        distance_miles=payload.estimated_distance_miles,
        weight_lbs=payload.weight_lbs,
        urgency=payload.urgency,
    )
    load = Load(
        shipper_id=user.id,
        photo_urls=[],
        calculated_price_cents=price,
        status=LoadStatus.posted,
        **payload.model_dump(),
    )
    db.add(load)
    await db.commit()
    await db.refresh(load)
    return load


@router.get("", response_model=list[LoadRead])
async def list_loads(
    city: str | None = Query(default=None, description="Filter by pickup city"),
    state: str | None = Query(default=None, description="Filter by pickup state"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(current_user),
) -> list[Load]:
    stmt = select(Load).where(Load.status == LoadStatus.posted).order_by(Load.created_at.desc())
    if city:
        stmt = stmt.where(Load.pickup_city == city)
    if state:
        stmt = stmt.where(Load.pickup_state == state)
    result = await db.scalars(stmt)
    return list(result)


@router.get("/{load_id}", response_model=LoadRead)
async def get_load(
    load_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(current_user),
) -> Load:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    return load


@router.patch("/{load_id}", response_model=LoadRead)
async def update_load(
    load_id: str,
    payload: LoadUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    load = await _get_owned_load(load_id, user, db)
    if load.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot edit load in status '{load.status.value}'",
        )

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(load, field, value)

    if PRICE_RELEVANT_FIELDS & updates.keys():
        load.calculated_price_cents = calculate_price_cents(
            distance_miles=load.estimated_distance_miles,
            weight_lbs=load.weight_lbs,
            urgency=load.urgency,
        )

    await db.commit()
    await db.refresh(load)
    return load


@router.delete("/{load_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_load_pre_acceptance(
    load_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Shipper takes down a load before anyone accepts it. Post-acceptance cancels use POST /cancel."""
    load = await _get_owned_load(load_id, user, db)
    if load.status not in CANCELLABLE_BY_SHIPPER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Use POST /cancel; load is in status '{load.status.value}'",
        )
    await booking.cancel_load(db, load, user)
    await db.commit()


@router.post("/{load_id}/accept", response_model=LoadRead)
async def accept_load_route(
    load_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    await booking.accept_load(db, load, user)
    await db.commit()
    await db.refresh(load)
    return load


@router.post("/{load_id}/pickup", response_model=LoadRead)
async def pickup_load_route(
    load_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    await booking.mark_picked_up(db, load, user)
    await db.commit()
    await db.refresh(load)
    return load


@router.post("/{load_id}/in-transit", response_model=LoadRead)
async def in_transit_load_route(
    load_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    await booking.mark_in_transit(db, load, user)
    await db.commit()
    await db.refresh(load)
    return load


@router.post("/{load_id}/deliver", response_model=LoadRead)
async def deliver_load_route(
    load_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    await booking.mark_delivered(db, load, user)
    await db.commit()
    await db.refresh(load)
    return load


@router.post("/{load_id}/cancel", response_model=LoadRead)
async def cancel_load_route(
    load_id: str,
    payload: CancelRequest | None = None,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    reason = payload.reason if payload else None
    await booking.cancel_load(db, load, user, reason=reason)
    await db.commit()
    await db.refresh(load)
    return load


@router.get("/{load_id}/payment", response_model=PaymentRead)
async def get_load_payment(
    load_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Payment:
    load = await db.get(Load, load_id)
    if load is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Load not found")
    if user.id not in {load.shipper_id, load.hauler_id}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the shipper or assigned hauler can view payment details",
        )
    payment = await db.scalar(
        select(Payment).where(Payment.load_id == load_id).order_by(Payment.created_at.desc()).limit(1)
    )
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No payment for this load")
    return payment


@router.post("/{load_id}/photos", response_model=LoadRead)
async def upload_load_photo(
    load_id: str,
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Load:
    load = await _get_owned_load(load_id, user, db)
    if load.status not in EDITABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot add photos to a load that's no longer editable",
        )
    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Empty file"
        )
    url = upload_file(bucket="loads", data=data, filename=file.filename or "photo", folder=load.id)
    load.photo_urls = [*load.photo_urls, url]
    await db.commit()
    await db.refresh(load)
    return load
