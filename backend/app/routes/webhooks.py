import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.user import UserProfile
from app.services import payments

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if stripe_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe-Signature header"
        )
    payload = await request.body()
    event = payments.construct_webhook_event(payload, stripe_signature)

    handler = _HANDLERS.get(event.type)
    if handler is None:
        logger.info("ignoring unhandled stripe event: %s", event.type)
        return {"status": "ignored", "type": event.type}

    await handler(db, event.data.object)
    await db.commit()
    return {"status": "ok", "type": event.type}


async def _handle_account_updated(db: AsyncSession, account: dict) -> None:
    account_id = account.get("id")
    if account_id is None:
        return
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.stripe_connect_account_id == account_id)
    )
    if profile is None:
        logger.warning("account.updated for unknown stripe_connect_account_id %s", account_id)


async def _handle_payment_intent_succeeded(db: AsyncSession, intent: dict) -> None:
    intent_id = intent.get("id")
    if intent_id is None:
        return
    payment = await db.scalar(
        select(Payment).where(Payment.stripe_payment_intent_id == intent_id)
    )
    if payment is None:
        logger.warning("payment_intent.succeeded for unknown intent %s", intent_id)
        return
    payment.status = PaymentStatus.captured


async def _handle_payment_intent_failed(db: AsyncSession, intent: dict) -> None:
    intent_id = intent.get("id")
    if intent_id is None:
        return
    payment = await db.scalar(
        select(Payment).where(Payment.stripe_payment_intent_id == intent_id)
    )
    if payment is None:
        logger.warning("payment_intent.payment_failed for unknown intent %s", intent_id)
        return
    last_error = intent.get("last_payment_error") or {}
    payment.status = PaymentStatus.failed
    payment.error_message = last_error.get("message", "Payment failed")
    logger.info(
        "payment_intent.payment_failed: payment %s marked failed for intent %s",
        payment.id, intent_id,
    )


_HANDLERS = {
    "account.updated": _handle_account_updated,
    "payment_intent.succeeded": _handle_payment_intent_succeeded,
    "payment_intent.payment_failed": _handle_payment_intent_failed,
}
