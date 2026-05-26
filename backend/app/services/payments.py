"""Stripe Connect payment service.

When settings.stripe_secret_key is None we run in 'bookkeeping-only' mode: Payment
rows are still written so the booking flow has a complete audit trail, but no real
Stripe API calls happen. Set STRIPE_SECRET_KEY in .env to enable real charges/transfers.
"""

import logging
from datetime import UTC, datetime

import stripe
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.load import Load
from app.models.payment import Payment, PaymentStatus
from app.models.user import User

logger = logging.getLogger(__name__)


def _stripe_enabled() -> bool:
    if settings.stripe_secret_key is None:
        return False
    stripe.api_key = settings.stripe_secret_key
    return True


def calculate_platform_fee_cents(amount_cents: int) -> int:
    return amount_cents * settings.platform_fee_bps // 10000


# ---------------------------------------------------------------------------
# Connect onboarding
# ---------------------------------------------------------------------------


async def create_connect_onboarding_link(db: AsyncSession, user: User) -> str:
    """Create (if needed) a Stripe Express account for a hauler and return an onboarding URL."""
    if not _stripe_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured on this server",
        )

    if user.profile.stripe_connect_account_id is None:
        account = stripe.Account.create(
            type="express",
            email=user.email,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
        )
        user.profile.stripe_connect_account_id = account.id
        await db.flush()

    link = stripe.AccountLink.create(
        account=user.profile.stripe_connect_account_id,
        refresh_url=settings.stripe_connect_refresh_url,
        return_url=settings.stripe_connect_return_url,
        type="account_onboarding",
    )
    return link.url


# ---------------------------------------------------------------------------
# Booking lifecycle integration
# ---------------------------------------------------------------------------


async def authorize_payment_for_load(db: AsyncSession, load: Load) -> Payment:
    """Called from booking.accept_load. Creates a Payment row; with Stripe enabled,
    also creates a PaymentIntent (manual capture) so funds are held until delivery.

    Note: real Stripe authorization requires a saved Customer + PaymentMethod for
    the shipper — those are wired in a future iteration. For now, when Stripe is
    enabled we log the intent but leave the actual PI creation for that follow-up.
    """
    fee = calculate_platform_fee_cents(load.calculated_price_cents)
    payment = Payment(
        load_id=load.id,
        amount_cents=load.calculated_price_cents,
        platform_fee_cents=fee,
        hauler_payout_cents=load.calculated_price_cents - fee,
        status=PaymentStatus.pending,
    )
    db.add(payment)

    if _stripe_enabled():
        # TODO: requires shipper Customer + PaymentMethod ids. Wire when we add
        # the "save card" flow on the frontend.
        logger.info(
            "stripe enabled but PaymentIntent creation deferred (no saved PM yet) for load %s",
            load.id,
        )

    return payment


async def capture_and_transfer(db: AsyncSession, load: Load) -> Payment | None:
    """Called from booking.mark_delivered. Captures the PaymentIntent and transfers
    the hauler's share to their Connect account.
    """
    payment = await db.scalar(
        select(Payment)
        .where(Payment.load_id == load.id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    if payment is None:
        logger.warning("no payment row for delivered load %s", load.id)
        return None

    if _stripe_enabled() and payment.stripe_payment_intent_id:
        try:
            stripe.PaymentIntent.capture(payment.stripe_payment_intent_id)
            payment.captured_at = datetime.now(UTC)
            payment.status = PaymentStatus.captured

            hauler_account_id = load.hauler.profile.stripe_connect_account_id if load.hauler else None
            if hauler_account_id:
                transfer = stripe.Transfer.create(
                    amount=payment.hauler_payout_cents,
                    currency="usd",
                    destination=hauler_account_id,
                    transfer_group=load.id,
                )
                payment.stripe_transfer_id = transfer.id
                payment.transferred_at = datetime.now(UTC)
                payment.status = PaymentStatus.transferred
            else:
                logger.warning(
                    "hauler %s has no stripe_connect_account_id; capture done, transfer skipped",
                    load.hauler_id,
                )
        except stripe.StripeError as e:
            logger.exception("stripe capture/transfer failed for load %s", load.id)
            payment.status = PaymentStatus.failed
            payment.error_message = str(e)
    else:
        # Bookkeeping-only path: mark completed so the audit trail is intact.
        now = datetime.now(UTC)
        payment.captured_at = now
        payment.transferred_at = now
        payment.status = PaymentStatus.transferred

    return payment


async def refund_on_cancel(db: AsyncSession, load: Load) -> Payment | None:
    """Called from booking.cancel_load when a load is cancelled after acceptance."""
    payment = await db.scalar(
        select(Payment)
        .where(Payment.load_id == load.id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    if payment is None:
        return None

    if _stripe_enabled() and payment.stripe_payment_intent_id:
        try:
            stripe.Refund.create(payment_intent=payment.stripe_payment_intent_id)
        except stripe.StripeError as e:
            logger.exception("stripe refund failed for load %s", load.id)
            payment.error_message = str(e)
            payment.status = PaymentStatus.failed
            return payment

    payment.status = PaymentStatus.refunded
    payment.refunded_at = datetime.now(UTC)
    return payment


# ---------------------------------------------------------------------------
# Webhook handling
# ---------------------------------------------------------------------------


def construct_webhook_event(payload: bytes, signature: str) -> stripe.Event:
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )
    try:
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
