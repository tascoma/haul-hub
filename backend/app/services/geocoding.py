"""Forward geocoding via the Google Maps Geocoding API.

Resolves a street address to `(lat, lng, place_id)`. Used when a load is posted so
pickup/dropoff `addresses` rows carry coordinates (the PostGIS `geom` column then syncs
via the migration-0008 trigger, and clients can plot the route).

Designed to never break the post-load path: any failure — no API key, network error,
zero results — returns ``None`` and the caller stores the address without coordinates.
"""

import logging
from decimal import Decimal

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_TIMEOUT_SECONDS = 5.0


async def geocode(
    *,
    line1: str,
    city: str,
    state: str,
    postal_code: str,
    country: str = "US",
) -> tuple[Decimal, Decimal, str] | None:
    """Return ``(lat, lng, place_id)`` for an address, or ``None`` if it can't be resolved.

    Returns ``None`` (rather than raising) on a missing key, transport error, or any
    non-``OK`` response so callers can treat geocoding as best-effort.
    """
    if not settings.google_maps_api_key:
        return None

    address = f"{line1}, {city}, {state} {postal_code}, {country}"
    params = {"address": address, "key": settings.google_maps_api_key}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.get(_GEOCODE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Geocoding request failed for %r: %s", address, exc)
        return None

    status = data.get("status")
    results = data.get("results") or []
    if status != "OK" or not results:
        logger.info("Geocoding returned %s for %r (no usable result)", status, address)
        return None

    top = results[0]
    location = top.get("geometry", {}).get("location", {})
    lat = location.get("lat")
    lng = location.get("lng")
    place_id = top.get("place_id")
    if lat is None or lng is None:
        return None

    return Decimal(str(lat)), Decimal(str(lng)), place_id
