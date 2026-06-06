"""Geocoding service + its opt-in wiring into find_or_create_address.

The geocoder is never called against the real Google API here: tests either rely on
the offline default (no API key in the suite) or monkeypatch the service to return a
canned result.
"""

from decimal import Decimal

from sqlalchemy import text

from app.databases import AsyncSessionLocal
from app.services import addresses, geocoding


async def test_geocode_returns_none_without_api_key() -> None:
    # The test suite sets no GOOGLE_MAPS_API_KEY, so geocoding is a no-op.
    result = await geocoding.geocode(
        line1="1 Market St", city="San Francisco", state="CA", postal_code="94105"
    )
    assert result is None


async def test_find_or_create_geocodes_new_row_when_enabled(monkeypatch) -> None:
    async def fake_geocode(**_kwargs):
        return Decimal("30.2672"), Decimal("-97.7431"), "place-abc"

    monkeypatch.setattr(geocoding, "geocode", fake_geocode)

    async with AsyncSessionLocal() as db:
        addr = await addresses.find_or_create_address(
            db,
            line1="1 Congress Ave",
            city="Austin",
            state="TX",
            postal_code="78701",
            geocode_if_missing=True,
        )
        await db.commit()

    assert addr.lat == Decimal("30.2672")
    assert addr.lng == Decimal("-97.7431")
    assert addr.place_id == "place-abc"


async def test_find_or_create_leaves_coords_null_when_geocode_fails(monkeypatch) -> None:
    async def fake_geocode(**_kwargs):
        return None

    monkeypatch.setattr(geocoding, "geocode", fake_geocode)

    async with AsyncSessionLocal() as db:
        addr = await addresses.find_or_create_address(
            db,
            line1="999 Nowhere Rd",
            city="Austin",
            state="TX",
            postal_code="78702",
            geocode_if_missing=True,
        )
        await db.commit()

    assert addr.lat is None
    assert addr.lng is None


async def test_dedup_hit_does_not_call_geocoder(monkeypatch) -> None:
    calls = {"n": 0}

    async def counting_geocode(**_kwargs):
        calls["n"] += 1
        return Decimal("1.0"), Decimal("2.0"), "place-1"

    monkeypatch.setattr(geocoding, "geocode", counting_geocode)

    async with AsyncSessionLocal() as db:
        await addresses.find_or_create_address(
            db,
            line1="1 Repeat St",
            city="Austin",
            state="TX",
            postal_code="78701",
            geocode_if_missing=True,
        )
        await db.commit()
        # Second call with identical canonical key reuses the row — no geocode.
        await addresses.find_or_create_address(
            db,
            line1="1 Repeat St",
            city="Austin",
            state="TX",
            postal_code="78701",
            geocode_if_missing=True,
        )
        await db.commit()

        count = (await db.execute(text("SELECT COUNT(*) FROM addresses"))).scalar_one()

    assert count == 1
    assert calls["n"] == 1
