"""Booking lifecycle state machine.

Every public function:
- Validates the actor is allowed to perform the transition.
- Validates the load is in an acceptable current state.
- Mutates the load + writes a BookingEvent row in the same session.
- Caller is responsible for committing the session.
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking_event import BookingEvent, BookingEventType
from app.models.load import Load, LoadStatus
from app.models.user import User
from app.services import payments

TERMINAL_STATUSES = {LoadStatus.delivered, LoadStatus.cancelled}


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _require_hauler_role(user: User) -> None:
    if not user.profile.hauler_enabled or user.hauler_profile is None:
        raise _forbidden("Hauler role not enabled")


def _require_assigned_hauler(load: Load, user: User) -> None:
    if load.hauler_id != user.id:
        raise _forbidden("You are not the assigned hauler for this load")


async def _log_event(
    db: AsyncSession,
    load: Load,
    actor: User,
    event_type: BookingEventType,
    metadata: dict | None = None,
) -> None:
    db.add(
        BookingEvent(
            load_id=load.id,
            actor_user_id=actor.id,
            event_type=event_type,
            event_metadata=metadata or {},
        )
    )


async def accept_load(db: AsyncSession, load: Load, hauler: User) -> Load:
    _require_hauler_role(hauler)
    if load.shipper_id == hauler.id:
        raise _forbidden("You cannot accept your own load")
    if load.status != LoadStatus.posted:
        raise _conflict(f"Load is in status '{load.status.value}', expected 'posted'")

    load.status = LoadStatus.accepted
    load.hauler_id = hauler.id
    load.accepted_at = datetime.now(UTC)
    await _log_event(db, load, hauler, BookingEventType.accepted)
    await payments.authorize_payment_for_load(db, load)
    return load


async def mark_picked_up(db: AsyncSession, load: Load, hauler: User) -> Load:
    _require_assigned_hauler(load, hauler)
    if load.status != LoadStatus.accepted:
        raise _conflict(f"Load is in status '{load.status.value}', expected 'accepted'")

    load.status = LoadStatus.picked_up
    load.picked_up_at = datetime.now(UTC)
    await _log_event(db, load, hauler, BookingEventType.picked_up)
    return load


async def mark_in_transit(db: AsyncSession, load: Load, hauler: User) -> Load:
    _require_assigned_hauler(load, hauler)
    if load.status != LoadStatus.picked_up:
        raise _conflict(f"Load is in status '{load.status.value}', expected 'picked_up'")

    load.status = LoadStatus.in_transit
    await _log_event(db, load, hauler, BookingEventType.in_transit)
    return load


async def mark_delivered(db: AsyncSession, load: Load, hauler: User) -> Load:
    _require_assigned_hauler(load, hauler)
    if load.status != LoadStatus.in_transit:
        raise _conflict(f"Load is in status '{load.status.value}', expected 'in_transit'")

    load.status = LoadStatus.delivered
    load.delivered_at = datetime.now(UTC)
    await _log_event(db, load, hauler, BookingEventType.delivered)
    await payments.capture_and_transfer(db, load)
    return load


async def cancel_load(
    db: AsyncSession, load: Load, actor: User, *, reason: str | None = None
) -> Load:
    if load.status in TERMINAL_STATUSES:
        raise _conflict(f"Load already in terminal status '{load.status.value}'")

    is_shipper = actor.id == load.shipper_id
    is_assigned_hauler = load.hauler_id is not None and actor.id == load.hauler_id
    if not (is_shipper or is_assigned_hauler):
        raise _forbidden("Only the shipper or assigned hauler can cancel a load")

    was_accepted = load.status not in {LoadStatus.draft, LoadStatus.posted}
    load.status = LoadStatus.cancelled
    load.cancelled_at = datetime.now(UTC)
    metadata = {"actor_role": "shipper" if is_shipper else "hauler"}
    if reason:
        metadata["reason"] = reason
    await _log_event(db, load, actor, BookingEventType.cancelled, metadata)
    if was_accepted:
        await payments.refund_on_cancel(db, load)
    return load
