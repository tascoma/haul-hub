"""Helpers for the normalized `addresses` table.

The PostGIS `geom` column is kept in sync with `lat`/`lng` by a database trigger
installed in migration 0008, so callers don't need to know PostGIS to write rows.
"""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address


async def find_or_create_address(
    db: AsyncSession,
    *,
    line1: str,
    city: str,
    state: str,
    postal_code: str,
    line2: str | None = None,
    country: str = "US",
    lat: Decimal | float | None = None,
    lng: Decimal | float | None = None,
    place_id: str | None = None,
) -> Address:
    """Return an existing `addresses` row matching the canonical key or create one.

    Dedup key is `(line1, postal_code, city)` — narrow enough to avoid collisions
    between similar suite numbers, broad enough that `1 Main St / 94110 / SF`
    only ever has one row regardless of how lat/lng came back from the geocoder.
    """
    stmt = (
        select(Address)
        .where(Address.line1 == line1)
        .where(Address.postal_code == postal_code)
        .where(Address.city == city)
        .limit(1)
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        return existing

    address = Address(
        line1=line1,
        line2=line2,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
        lat=Decimal(str(lat)) if lat is not None else None,
        lng=Decimal(str(lng)) if lng is not None else None,
        place_id=place_id,
    )
    db.add(address)
    await db.flush()
    return address
