"""Delete everything a simulation run created, in FK-safe order.

Matches rows by the run-id markers embedded in load titles and user emails (see
config.py). Connect accounts created on Stripe are left in place — they are test
accounts and Stripe has no bulk-delete; pass their ids if you want to clean them.
"""

from __future__ import annotations

import logging

from . import config

logger = logging.getLogger("sim.cleanup")


async def cleanup(run_id: str) -> dict[str, int]:
    """Remove sim users, loads, payments, events, and hauler profiles for run_id."""
    from sqlalchemy import delete, select

    from app.databases import AsyncSessionLocal
    from app.models.booking_event import BookingEvent
    from app.models.load import Load
    from app.models.payment import Payment
    from app.models.user import HaulerProfile, User, UserProfile

    deleted: dict[str, int] = {}
    async with AsyncSessionLocal() as db:
        load_ids = list(await db.scalars(
            select(Load.id).where(Load.title.like(config.title_marker(run_id)))
        ))
        user_ids = list(await db.scalars(
            select(User.id).where(User.email.like(config.email_marker(run_id)))
        ))

        if load_ids:
            deleted["payments"] = (await db.execute(
                delete(Payment).where(Payment.load_id.in_(load_ids)))).rowcount
            deleted["booking_events"] = (await db.execute(
                delete(BookingEvent).where(BookingEvent.load_id.in_(load_ids)))).rowcount
            deleted["loads"] = (await db.execute(
                delete(Load).where(Load.id.in_(load_ids)))).rowcount
        if user_ids:
            deleted["hauler_profiles"] = (await db.execute(
                delete(HaulerProfile).where(HaulerProfile.user_id.in_(user_ids)))).rowcount
            deleted["user_profiles"] = (await db.execute(
                delete(UserProfile).where(UserProfile.user_id.in_(user_ids)))).rowcount
            deleted["users"] = (await db.execute(
                delete(User).where(User.id.in_(user_ids)))).rowcount
        await db.commit()

    logger.info("cleanup run=%s removed=%s", run_id, deleted)
    return deleted
