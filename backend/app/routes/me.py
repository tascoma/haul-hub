from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases import get_db
from app.dependencies.auth import current_user
from app.models.address import Address, SavedAddress
from app.models.hauler_document import HaulerDocument
from app.models.identity_verification import IdentityVerification
from app.models.load import Load
from app.models.service_area import ServiceArea
from app.models.terms_acceptance import TermsAcceptance
from app.models.user import HaulerProfile, User
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.address import (
    AddressCreate,
    AddressRead,
    AddressUpdate,
    SavedAddressCreate,
    SavedAddressRead,
    SavedAddressUpdate,
)
from app.schemas.hauler_document import HaulerDocumentCreate, HaulerDocumentRead
from app.schemas.identity_verification import (
    IdentityVerificationCreate,
    IdentityVerificationRead,
)
from app.schemas.load import LoadRead
from app.schemas.onboarding import OnboardingChecks, OnboardingStatus, OnboardingStep
from app.schemas.payment import ConnectOnboardingResponse
from app.schemas.service_area import ServiceAreaCreate, ServiceAreaRead
from app.schemas.terms_acceptance import TermsAcceptanceCreate, TermsAcceptanceRead
from app.schemas.auth import ChangePasswordRequest
from app.schemas.user import (
    HaulerProfileCreate,
    HaulerProfileRead,
    HaulerProfileUpdate,
    MeRead,
    UserProfileUpdate,
)
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.services import payments
from app.services.auth import hash_password, verify_password
from app.services.hauler import ensure_hauler_profile

router = APIRouter()


# ─── Identity ──────────────────────────────────────────────────────────────

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


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.password_hash = hash_password(payload.new_password)
    await db.commit()


# ─── Hauler profile (operational only — vehicles managed separately) ──────

@router.post("/enable-hauler", response_model=HaulerProfileRead)
async def enable_hauler(
    payload: HaulerProfileCreate,
    response: Response,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> HaulerProfile:
    """Idempotent. Returns 201 if a HaulerProfile was created, 200 if one already existed."""
    hauler, created = await ensure_hauler_profile(db, user, payload)
    await db.commit()
    await db.refresh(hauler)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return hauler


@router.get("/onboarding-status", response_model=OnboardingStatus)
async def onboarding_status(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> OnboardingStatus:
    profile_complete = bool(user.profile.full_name) and bool(user.profile.phone)

    has_vehicle = False
    has_service_area = False
    if user.profile.hauler_enabled:
        vehicle_count = await db.scalar(
            select(func.count())
            .select_from(Vehicle)
            .where(
                Vehicle.owner_user_id == user.id,
                Vehicle.status != VehicleStatus.retired,
            )
        )
        has_vehicle = bool(vehicle_count)
        hp = user.hauler_profile
        has_service_area = (
            hp is not None
            and hp.home_base_address_id is not None
            and hp.service_radius_miles is not None
        )

    customer_ready = user.profile.shipper_enabled and profile_complete
    hauler_ready = (
        user.profile.hauler_enabled
        and profile_complete
        and has_vehicle
        and has_service_area
    )

    next_step: OnboardingStep
    if not profile_complete:
        next_step = "profile"
    elif user.profile.hauler_enabled and user.hauler_profile is None:
        next_step = "hauler_profile"
    elif user.profile.hauler_enabled and not has_vehicle:
        next_step = "hauler_vehicle"
    elif user.profile.hauler_enabled and not has_service_area:
        next_step = "hauler_service_area"
    else:
        next_step = "done"

    return OnboardingStatus(
        profile_complete=profile_complete,
        customer_ready=customer_ready,
        hauler_ready=hauler_ready,
        next_step=next_step,
        checks=OnboardingChecks(
            has_vehicle=has_vehicle,
            has_service_area=has_service_area,
        ),
    )


@router.get("/hauler-profile", response_model=HaulerProfileRead)
async def read_hauler_profile(user: User = Depends(current_user)) -> HaulerProfile:
    if user.hauler_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hauler profile not enabled"
        )
    return user.hauler_profile


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


# ─── Loads / hauls ─────────────────────────────────────────────────────────

@router.get("/loads", response_model=list[LoadRead])
async def my_loads(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[Load]:
    """All loads the current user posted, in any status, newest first."""
    result = await db.scalars(
        select(Load).where(Load.shipper_id == user.id).order_by(Load.created_at.desc())
    )
    return list(result)


@router.get("/hauls", response_model=list[LoadRead])
async def my_hauls(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[Load]:
    """All loads the current user has accepted as the hauler, in any status, newest first."""
    result = await db.scalars(
        select(Load).where(Load.hauler_id == user.id).order_by(Load.created_at.desc())
    )
    return list(result)


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


# ─── Vehicles ──────────────────────────────────────────────────────────────

@router.get("/vehicles", response_model=list[VehicleRead])
async def list_vehicles(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[Vehicle]:
    result = await db.scalars(
        select(Vehicle)
        .where(Vehicle.owner_user_id == user.id)
        .order_by(Vehicle.created_at.desc())
    )
    return list(result)


@router.post(
    "/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED
)
async def create_vehicle(
    payload: VehicleCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Vehicle:
    data = payload.model_dump()
    is_default = data.get("is_default", False)
    if is_default:
        await _clear_default_vehicle(db, user.id)

    vehicle = Vehicle(owner_user_id=user.id, **data)
    db.add(vehicle)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only one vehicle may be marked default per hauler",
        ) from exc
    await db.refresh(vehicle)
    return vehicle


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle(
    vehicle_id: str,
    payload: VehicleUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Vehicle:
    vehicle = await _get_owned_vehicle(db, vehicle_id, user)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("is_default") is True:
        await _clear_default_vehicle(db, user.id, except_id=vehicle.id)

    for field, value in updates.items():
        setattr(vehicle, field, value)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    vehicle = await _get_owned_vehicle(db, vehicle_id, user)
    # Soft-retire — keep history for loads that referenced this vehicle.
    vehicle.status = VehicleStatus.retired
    vehicle.is_default = False
    await db.commit()


async def _get_owned_vehicle(db: AsyncSession, vehicle_id: str, user: User) -> Vehicle:
    vehicle = await db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.owner_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


async def _clear_default_vehicle(
    db: AsyncSession, owner_id: str, except_id: str | None = None
) -> None:
    """Flip any current default to non-default so the partial unique index lets us set a new one."""
    stmt = select(Vehicle).where(
        Vehicle.owner_user_id == owner_id, Vehicle.is_default.is_(True)
    )
    current = (await db.scalars(stmt)).all()
    for v in current:
        if v.id != except_id:
            v.is_default = False
    if current:
        await db.flush()


# ─── Saved address book ────────────────────────────────────────────────────

@router.get("/addresses", response_model=list[SavedAddressRead])
async def list_saved_addresses(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[SavedAddress]:
    result = await db.scalars(
        select(SavedAddress)
        .where(SavedAddress.user_id == user.id)
        .order_by(SavedAddress.created_at.desc())
    )
    return list(result)


@router.post(
    "/addresses/raw", response_model=AddressRead, status_code=status.HTTP_201_CREATED
)
async def create_address(
    payload: AddressCreate,
    _user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Address:
    """Insert a new address row directly (without saving it to the user's book).

    Useful for shipper flows that need an address_id before posting a load.
    """
    address = Address(**payload.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


@router.post(
    "/addresses", response_model=SavedAddressRead, status_code=status.HTTP_201_CREATED
)
async def save_address(
    payload: SavedAddressCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedAddress:
    address = await db.get(Address, payload.address_id)
    if address is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Address not found"
        )

    if payload.is_default_pickup:
        await _clear_default_saved(db, user.id, field="is_default_pickup")
    if payload.is_default_dropoff:
        await _clear_default_saved(db, user.id, field="is_default_dropoff")

    saved = SavedAddress(user_id=user.id, **payload.model_dump())
    db.add(saved)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Default address conflict",
        ) from exc
    await db.refresh(saved)
    return saved


@router.patch("/addresses/{saved_id}", response_model=SavedAddressRead)
async def update_saved_address(
    saved_id: str,
    payload: SavedAddressUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedAddress:
    saved = await _get_owned_saved_address(db, saved_id, user)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("is_default_pickup") is True:
        await _clear_default_saved(db, user.id, field="is_default_pickup", except_id=saved.id)
    if updates.get("is_default_dropoff") is True:
        await _clear_default_saved(db, user.id, field="is_default_dropoff", except_id=saved.id)
    for field, value in updates.items():
        setattr(saved, field, value)
    await db.commit()
    await db.refresh(saved)
    return saved


@router.delete("/addresses/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_address(
    saved_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    saved = await _get_owned_saved_address(db, saved_id, user)
    await db.delete(saved)
    await db.commit()


async def _get_owned_saved_address(
    db: AsyncSession, saved_id: str, user: User
) -> SavedAddress:
    saved = await db.get(SavedAddress, saved_id)
    if saved is None or saved.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved address not found"
        )
    return saved


async def _clear_default_saved(
    db: AsyncSession, user_id: str, *, field: str, except_id: str | None = None
) -> None:
    stmt = select(SavedAddress).where(
        SavedAddress.user_id == user_id, getattr(SavedAddress, field).is_(True)
    )
    rows = (await db.scalars(stmt)).all()
    for r in rows:
        if r.id != except_id:
            setattr(r, field, False)
    if rows:
        await db.flush()


# ─── Hauler documents ──────────────────────────────────────────────────────

@router.get("/documents", response_model=list[HaulerDocumentRead])
async def list_documents(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[HaulerDocument]:
    result = await db.scalars(
        select(HaulerDocument)
        .where(HaulerDocument.hauler_user_id == user.id)
        .order_by(HaulerDocument.created_at.desc())
    )
    return list(result)


@router.post(
    "/documents", response_model=HaulerDocumentRead, status_code=status.HTTP_201_CREATED
)
async def create_document(
    payload: HaulerDocumentCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> HaulerDocument:
    doc = HaulerDocument(hauler_user_id=user.id, **payload.model_dump())
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


# ─── Identity verifications ────────────────────────────────────────────────

@router.get("/verifications", response_model=list[IdentityVerificationRead])
async def list_verifications(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[IdentityVerification]:
    result = await db.scalars(
        select(IdentityVerification)
        .where(IdentityVerification.user_id == user.id)
        .order_by(IdentityVerification.created_at.desc())
    )
    return list(result)


@router.post(
    "/verifications",
    response_model=IdentityVerificationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_verification(
    payload: IdentityVerificationCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> IdentityVerification:
    verification = IdentityVerification(
        user_id=user.id,
        submitted_at=datetime.now(UTC),
        **payload.model_dump(),
    )
    db.add(verification)
    await db.commit()
    await db.refresh(verification)
    return verification


# ─── Terms acceptances ─────────────────────────────────────────────────────

@router.post(
    "/terms-acceptances",
    response_model=TermsAcceptanceRead,
    status_code=status.HTTP_201_CREATED,
)
async def record_terms_acceptance(
    payload: TermsAcceptanceCreate,
    request: Request,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> TermsAcceptance:
    acceptance = TermsAcceptance(
        user_id=user.id,
        document_kind=payload.document_kind,
        version=payload.version,
        accepted_at=datetime.now(UTC),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(acceptance)
    await db.commit()
    await db.refresh(acceptance)
    return acceptance


# ─── Service areas ─────────────────────────────────────────────────────────

@router.get("/service-areas", response_model=list[ServiceAreaRead])
async def list_service_areas(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[ServiceArea]:
    result = await db.scalars(
        select(ServiceArea)
        .where(ServiceArea.hauler_user_id == user.id)
        .order_by(ServiceArea.created_at.desc())
    )
    return list(result)


@router.post(
    "/service-areas",
    response_model=ServiceAreaRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_service_area(
    payload: ServiceAreaCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> ServiceArea:
    area = ServiceArea(hauler_user_id=user.id, **payload.model_dump())
    db.add(area)
    await db.commit()
    await db.refresh(area)
    return area
