"""Helpers for the normalized `addresses` table.

The PostGIS `geom` column is kept in sync with `lat`/`lng` by a database trigger
installed in migration 0008, so callers don't need to know PostGIS to write rows.
"""

from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.services import geocoding

_EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in miles between two lat/lng points.

    Used for radius filtering in Python so the same logic runs on SQLite (tests)
    and Postgres alike; the PostGIS `geom` column stays reserved for queries that
    need an index-backed spatial search.
    """
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return 2 * _EARTH_RADIUS_MILES * asin(sqrt(a))


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
    geocode_if_missing: bool = False,
) -> Address:
    """Return an existing `addresses` row matching the canonical key or create one.

    Dedup key is `(line1, postal_code, city)` — narrow enough to avoid collisions
    between similar suite numbers, broad enough that `1 Main St / 94110 / SF`
    only ever has one row regardless of how lat/lng came back from the geocoder.

    When `geocode_if_missing` is set and no coordinates were supplied, a *newly created*
    row is geocoded via the Google Maps service. Dedup hits are never geocoded (the
    existing row already has whatever coordinates it was created with), so repeat posts
    of the same address don't spend API calls.
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

    if geocode_if_missing and lat is None and lng is None:
        result = await geocoding.geocode(
            line1=line1, city=city, state=state, postal_code=postal_code, country=country
        )
        if result is not None:
            lat, lng, place_id = result

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
