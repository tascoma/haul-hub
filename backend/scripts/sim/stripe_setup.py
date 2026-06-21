"""Stripe test-mode setup helpers (used only when --stripe is enabled).

The Stripe SDK is synchronous, so every call is pushed to a worker thread to keep
the async harness responsive.

Connect: real Express onboarding needs the hosted UI, which can't be automated.
To get a payout-ready destination for the transfer leg we instead create an
instantly-enabled **Custom** test account here and write its id onto the hauler's
profile (see actors.set_connect_account). This is a test-only shortcut; it still
exercises the real authorize -> capture -> transfer path and the transfer.*
webhooks. The real POST /me/connect-onboarding endpoint is exercised separately
by the preflight check.
"""

from __future__ import annotations

import asyncio
import logging
import time

import stripe

from . import config

logger = logging.getLogger("sim.stripe_setup")


def init(secret_key: str) -> None:
    stripe.api_key = secret_key


# Card tokens that, once made into a real PaymentMethod, drive each outcome.
# decline uses the "attaches OK but charging fails" card (4000000000000341) so the
# failure lands on the PaymentIntent authorize, not on save_payment_method —
# tok_chargeDeclined is rejected at attach time and never reaches the booking flow.
_CARD_TOKENS = {
    "visa": "tok_visa",
    "decline": "tok_chargeCustomerFail",
    "dispute": config.DISPUTE_CARD_TOKEN,  # tok_createDispute
}


async def payment_method_for(kind: str) -> str:
    """Create a real PaymentMethod for the scenario and return its id.

    The magic shared tokens (e.g. pm_card_visa) can't be set as a customer's
    default after attach, so build a concrete pm_... from a card token instead.
    """
    token = _CARD_TOKENS.get(kind, "tok_visa")
    return await asyncio.to_thread(_create_pm, token)


def _create_pm(token: str) -> str:
    return stripe.PaymentMethod.create(type="card", card={"token": token}).id


async def create_enabled_connect_account(email: str) -> str:
    """Create a Custom connected account that is immediately charges/payouts enabled."""
    return await asyncio.to_thread(_create_enabled_connect_account, email)


def _create_enabled_connect_account(email: str) -> str:
    account = stripe.Account.create(
        type="custom",
        country="US",
        email=email,
        business_type="individual",
        capabilities={
            "card_payments": {"requested": True},
            "transfers": {"requested": True},
        },
        business_profile={
            "mcc": "4214",
            "url": "https://www.haulhubsim.com",
            "product_description": "Simulated hauling services",
        },
        individual={
            "first_name": "Test",
            "last_name": "Hauler",
            "email": email,
            "phone": "0000000000",
            "ssn_last_4": "0000",
            "id_number": "000000000",
            "dob": {"day": 1, "month": 1, "year": 1990},
            "address": {
                "line1": "address_full_match",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94103",
                "country": "US",
            },
        },
        tos_acceptance={"date": int(time.time()), "ip": "127.0.0.1"},
        external_account="btok_us_verified",
    )
    logger.info(
        "created connect account %s (charges=%s payouts=%s)",
        account.id,
        account.charges_enabled,
        account.payouts_enabled,
    )
    return account.id
