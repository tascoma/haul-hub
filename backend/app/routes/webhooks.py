import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.user import UserProfile
from app.models.webhook_event import ProcessedWebhookEvent
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

    event_id = event.get("id")
    # Stripe retries deliveries; ignore an event we've already processed.
    if event_id and await db.get(ProcessedWebhookEvent, event_id):
        logger.info("ignoring duplicate stripe event: %s", event_id)
        return {"status": "duplicate", "type": event.get("type")}

    handler = _HANDLERS.get(event["type"])
    if handler is None:
        logger.info("ignoring unhandled stripe event: %s", event["type"])
        return {"status": "ignored", "type": event["type"]}

    # Record the event in the same transaction as its side effects so a failed
    # handler does not mark the event processed.
    if event_id:
        db.add(ProcessedWebhookEvent(event_id=event_id))
    await handler(db, event)
    await db.commit()
    return {"status": "ok", "type": event["type"]}


async def _latest_payment_for_intent(db: AsyncSession, intent_id: str) -> Payment | None:
    return await db.scalar(
        select(Payment).where(Payment.stripe_payment_intent_id == intent_id)
    )


async def _latest_payment_for_load(db: AsyncSession, load_id: str) -> Payment | None:
    return await db.scalar(
        select(Payment)
        .where(Payment.load_id == load_id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )


async def _handle_account_updated(db: AsyncSession, event: dict) -> None:
    account = event["data"]["object"]
    account_id = account.get("id")
    if account_id is None:
        return
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.stripe_connect_account_id == account_id)
    )
    if profile is None:
        logger.warning("account.updated for unknown stripe_connect_account_id %s", account_id)
        return
    profile.stripe_charges_enabled = bool(account.get("charges_enabled"))
    profile.stripe_payouts_enabled = bool(account.get("payouts_enabled"))
    profile.stripe_details_submitted = bool(account.get("details_submitted"))
    logger.info(
        "account.updated: account=%s charges=%s payouts=%s details=%s",
        account_id,
        profile.stripe_charges_enabled,
        profile.stripe_payouts_enabled,
        profile.stripe_details_submitted,
    )


async def _handle_account_deauthorized(db: AsyncSession, event: dict) -> None:
    # The connected account id is on the event, not the (application) data object.
    account_id = event.get("account")
    if account_id is None:
        return
    profile = await db.scalar(
        select(UserProfile).where(UserProfile.stripe_connect_account_id == account_id)
    )
    if profile is None:
        logger.warning("account.application.deauthorized for unknown account %s", account_id)
        return
    profile.stripe_connect_account_id = None
    profile.stripe_charges_enabled = False
    profile.stripe_payouts_enabled = False
    profile.stripe_details_submitted = False
    logger.info("account.application.deauthorized: cleared Connect account %s", account_id)


async def _handle_payment_intent_succeeded(db: AsyncSession, event: dict) -> None:
    intent = event["data"]["object"]
    intent_id = intent.get("id")
    if intent_id is None:
        return
    payment = await _latest_payment_for_intent(db, intent_id)
    if payment is None:
        logger.warning("payment_intent.succeeded for unknown intent %s", intent_id)
        return
    # Forward-only: never regress a payment already marked transferred.
    if payments.advance_status(payment, PaymentStatus.captured):
        payment.captured_at = payment.captured_at or datetime.now(UTC)


async def _handle_payment_intent_failed(db: AsyncSession, event: dict) -> None:
    intent = event["data"]["object"]
    intent_id = intent.get("id")
    if intent_id is None:
        return
    payment = await _latest_payment_for_intent(db, intent_id)
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


async def _handle_charge_refunded(db: AsyncSession, event: dict) -> None:
    charge = event["data"]["object"]
    intent_id = charge.get("payment_intent")
    if intent_id is None:
        return
    payment = await _latest_payment_for_intent(db, intent_id)
    if payment is None:
        logger.warning("charge.refunded for unknown intent %s", intent_id)
        return
    if payment.status != PaymentStatus.refunded:
        payment.status = PaymentStatus.refunded
        payment.refunded_at = datetime.now(UTC)
        logger.info("charge.refunded: payment %s marked refunded", payment.id)


async def _handle_charge_dispute_created(db: AsyncSession, event: dict) -> None:
    dispute = event["data"]["object"]
    intent_id = dispute.get("payment_intent")
    payment = await _latest_payment_for_intent(db, intent_id) if intent_id else None
    # We don't have a dedicated dispute status; flag it for operator attention and
    # alert via logs so it surfaces in monitoring.
    if payment is not None:
        payment.error_message = f"Dispute opened: {dispute.get('reason', 'unknown')}"
    logger.warning(
        "charge.dispute.created: intent=%s amount=%s reason=%s payment=%s",
        intent_id,
        dispute.get("amount"),
        dispute.get("reason"),
        payment.id if payment else "UNKNOWN",
    )


async def _handle_transfer_created(db: AsyncSession, event: dict) -> None:
    transfer = event["data"]["object"]
    load_id = payments.load_id_from_transfer_group(transfer.get("transfer_group"))
    if load_id is None:
        return
    payment = await _latest_payment_for_load(db, load_id)
    if payment is None:
        logger.warning("transfer.created for unknown load %s", load_id)
        return
    if not payment.stripe_transfer_id:
        payment.stripe_transfer_id = transfer.get("id")
    if payments.advance_status(payment, PaymentStatus.transferred):
        payment.transferred_at = payment.transferred_at or datetime.now(UTC)
        logger.info("transfer.created: payment %s marked transferred", payment.id)


async def _handle_transfer_failed(db: AsyncSession, event: dict) -> None:
    transfer = event["data"]["object"]
    load_id = payments.load_id_from_transfer_group(transfer.get("transfer_group"))
    payment = await _latest_payment_for_load(db, load_id) if load_id else None
    # Funds were captured but the payout to the hauler failed — leave the payment
    # status alone (the shipper was charged) and flag for operator follow-up.
    if payment is not None:
        payment.error_message = "Transfer to hauler failed"
    logger.warning(
        "transfer.failed: load=%s transfer=%s payment=%s",
        load_id, transfer.get("id"), payment.id if payment else "UNKNOWN",
    )


_HANDLERS = {
    "account.updated": _handle_account_updated,
    "account.application.deauthorized": _handle_account_deauthorized,
    "payment_intent.succeeded": _handle_payment_intent_succeeded,
    "payment_intent.payment_failed": _handle_payment_intent_failed,
    "charge.refunded": _handle_charge_refunded,
    "charge.dispute.created": _handle_charge_dispute_created,
    "transfer.created": _handle_transfer_created,
    "transfer.failed": _handle_transfer_failed,
}
