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
# Customer management
# ---------------------------------------------------------------------------


async def get_or_create_customer(db: AsyncSession, user: User) -> str:
    """Return the shipper's Stripe Customer ID, creating one if needed."""
    if user.profile.stripe_customer_id:
        return user.profile.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": user.id},
    )
    user.profile.stripe_customer_id = customer.id
    await db.flush()
    return customer.id


async def create_setup_intent(db: AsyncSession, user: User) -> str:
    """Create a SetupIntent so the shipper can save a card without an immediate charge.
    Returns the client_secret to pass to Stripe.js on the frontend.
    """
    if not _stripe_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured on this server",
        )
    customer_id = await get_or_create_customer(db, user)
    intent = stripe.SetupIntent.create(
        customer=customer_id,
        payment_method_types=["card"],
    )
    return intent.client_secret


async def save_default_payment_method(
    db: AsyncSession, user: User, payment_method_id: str
) -> dict:
    """Attach a PaymentMethod to the shipper's Customer and set it as default.
    Returns basic card info (brand, last4, exp) for display.
    """
    if not _stripe_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured on this server",
        )
    customer_id = await get_or_create_customer(db, user)
    stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
    stripe.Customer.modify(
        customer_id,
        invoice_settings={"default_payment_method": payment_method_id},
    )
    user.profile.stripe_default_payment_method_id = payment_method_id
    await db.flush()

    pm = stripe.PaymentMethod.retrieve(payment_method_id)
    card = pm.card
    return {
        "brand": card.brand,
        "last4": card.last4,
        "exp_month": card.exp_month,
        "exp_year": card.exp_year,
    }


async def get_default_payment_method(user: User) -> dict | None:
    """Fetch saved card details for display. Returns None if no card saved."""
    if not _stripe_enabled():
        return None
    pm_id = user.profile.stripe_default_payment_method_id
    if not pm_id:
        return None
    try:
        pm = stripe.PaymentMethod.retrieve(pm_id)
    except stripe.InvalidRequestError:
        return None
    card = pm.card
    return {
        "brand": card.brand,
        "last4": card.last4,
        "exp_month": card.exp_month,
        "exp_year": card.exp_year,
    }


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


async def authorize_payment_for_load(db: AsyncSession, load: Load, hauler: User) -> Payment:
    """Called from booking.accept_load. Creates a Payment row; with Stripe enabled
    and a saved shipper PaymentMethod, creates a manual-capture PaymentIntent so
    funds are held until delivery.
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

    logger.info(
        "authorize_payment_for_load: load=%s amount=%d cents fee=%d cents hauler_payout=%d cents",
        load.id, payment.amount_cents, payment.platform_fee_cents, payment.hauler_payout_cents,
    )

    if not _stripe_enabled():
        logger.info("authorize_payment_for_load: Stripe disabled — bookkeeping-only mode")
        return payment

    pm_id = load.shipper.profile.stripe_default_payment_method_id
    customer_id = load.shipper.profile.stripe_customer_id
    hauler_connect_id = hauler.profile.stripe_connect_account_id

    logger.info(
        "authorize_payment_for_load: shipper=%s customer_id=%s pm_id=%s hauler=%s connect_id=%s",
        load.shipper_id,
        customer_id or "MISSING",
        pm_id or "MISSING",
        hauler.id,
        hauler_connect_id or "MISSING",
    )

    if not pm_id:
        logger.warning("authorize_payment_for_load: shipper has no saved payment method — bookkeeping-only")
        return payment
    if not customer_id:
        logger.warning("authorize_payment_for_load: shipper has no Stripe customer ID — bookkeeping-only")
        return payment
    if not hauler_connect_id:
        logger.warning("authorize_payment_for_load: hauler has no Stripe Connect account — bookkeeping-only")
        return payment

    try:
        logger.info("authorize_payment_for_load: creating PaymentIntent for load %s", load.id)
        intent = stripe.PaymentIntent.create(
            amount=payment.amount_cents,
            currency="usd",
            customer=customer_id,
            payment_method=pm_id,
            payment_method_types=["card"],
            confirm=True,
            capture_method="manual",
            application_fee_amount=payment.platform_fee_cents,
            transfer_data={"destination": hauler_connect_id},
        )
        payment.stripe_payment_intent_id = intent.id
        payment.status = PaymentStatus.authorized
        payment.authorized_at = datetime.now(UTC)
        logger.info(
            "authorize_payment_for_load: PaymentIntent %s created (status=%s) for load %s",
            intent.id, intent.status, load.id,
        )
    except stripe.StripeError as e:
        logger.exception("authorize_payment_for_load: PaymentIntent creation failed for load %s: %s", load.id, e)
        payment.status = PaymentStatus.failed
        payment.error_message = str(e)

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
        logger.warning("capture_and_transfer: no payment row for load %s", load.id)
        return None

    logger.info(
        "capture_and_transfer: load=%s payment=%s status=%s pi_id=%s",
        load.id, payment.id, payment.status, payment.stripe_payment_intent_id or "NONE",
    )

    if _stripe_enabled() and payment.stripe_payment_intent_id:
        try:
            logger.info("capture_and_transfer: capturing PaymentIntent %s", payment.stripe_payment_intent_id)
            # transfer_data on the PaymentIntent means Stripe automatically transfers
            # the hauler's share on capture — no separate Transfer.create needed.
            captured = stripe.PaymentIntent.capture(payment.stripe_payment_intent_id)
            payment.captured_at = datetime.now(UTC)

            # Pull the transfer ID from the captured charge if available.
            transfer_id = None
            latest_charge = getattr(captured, "latest_charge", None)
            if latest_charge:
                charge = stripe.Charge.retrieve(latest_charge) if isinstance(latest_charge, str) else latest_charge
                transfer_id = getattr(charge, "transfer", None)

            if transfer_id:
                payment.stripe_transfer_id = transfer_id
                payment.transferred_at = datetime.now(UTC)
                payment.status = PaymentStatus.transferred
                logger.info(
                    "capture_and_transfer: captured + transferred %s for load %s",
                    transfer_id, load.id,
                )
            else:
                payment.status = PaymentStatus.captured
                logger.info(
                    "capture_and_transfer: captured PaymentIntent %s (no transfer ID yet) for load %s",
                    payment.stripe_payment_intent_id, load.id,
                )
        except stripe.StripeError as e:
            logger.exception("capture_and_transfer: Stripe error for load %s: %s", load.id, e)
            payment.status = PaymentStatus.failed
            payment.error_message = str(e)
    else:
        logger.info(
            "capture_and_transfer: no PaymentIntent (bookkeeping-only) for load %s — marking transferred",
            load.id,
        )
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
        logger.info("refund_on_cancel: no payment row for load %s — nothing to refund", load.id)
        return None

    logger.info(
        "refund_on_cancel: load=%s payment=%s pi_id=%s",
        load.id, payment.id, payment.stripe_payment_intent_id or "NONE",
    )

    if _stripe_enabled() and payment.stripe_payment_intent_id:
        try:
            logger.info("refund_on_cancel: issuing refund for PaymentIntent %s", payment.stripe_payment_intent_id)
            stripe.Refund.create(payment_intent=payment.stripe_payment_intent_id)
            logger.info("refund_on_cancel: refund issued for load %s", load.id)
        except stripe.StripeError as e:
            logger.exception("refund_on_cancel: Stripe refund failed for load %s: %s", load.id, e)
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
