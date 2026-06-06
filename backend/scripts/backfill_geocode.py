"""Backfill lat/lng for `addresses` rows created before geocoding existed.

Selects every address with a NULL `lat`, geocodes it via the Google Maps service, and
writes the coordinates back (the migration-0008 trigger then fills `geom`). Idempotent:
re-running only touches rows that are still missing coordinates.

Run from the `backend/` directory with GOOGLE_MAPS_API_KEY set in the environment / .env:

    uv run python -m scripts.backfill_geocode

Pass --limit N to cap how many rows are processed in one run.
"""

import argparse
import asyncio
import logging

from sqlalchemy import select

from app.core.config import settings
from app.databases import AsyncSessionLocal
from app.models.address import Address
from app.services import geocoding

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("backfill_geocode")

# Google's standard tier allows ~50 requests/sec; stay well under it.
_DELAY_SECONDS = 0.1


async def backfill(limit: int | None) -> None:
    if not settings.google_maps_api_key:
        raise SystemExit("GOOGLE_MAPS_API_KEY is not set — nothing to geocode.")

    async with AsyncSessionLocal() as db:
        stmt = select(Address).where(Address.lat.is_(None))
        if limit is not None:
            stmt = stmt.limit(limit)
        addresses = (await db.execute(stmt)).scalars().all()

        logger.info("Found %d address(es) without coordinates", len(addresses))
        resolved = 0
        for addr in addresses:
            result = await geocoding.geocode(
                line1=addr.line1,
                city=addr.city,
                state=addr.state,
                postal_code=addr.postal_code,
                country=addr.country,
            )
            if result is None:
                logger.warning("Could not geocode %s, %s %s", addr.line1, addr.city, addr.state)
            else:
                addr.lat, addr.lng, addr.place_id = result
                resolved += 1
            await asyncio.sleep(_DELAY_SECONDS)

        await db.commit()
        logger.info("Geocoded %d of %d address(es)", resolved, len(addresses))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process this run")
    args = parser.parse_args()
    asyncio.run(backfill(args.limit))


if __name__ == "__main__":
    main()
