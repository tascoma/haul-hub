"""Payments in bookkeeping-only mode — no STRIPE_SECRET_KEY
(formerly scripts/smoke_phase4.py).

Real Stripe API integration is tested separately when
STRIPE_SECRET_KEY=sk_test_... is set.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.databases import AsyncSessionLocal
from app.models.payment import Payment
from app.services.payments import calculate_platform_fee_cents

pytestmark = pytest.mark.skipif(
    settings.stripe_secret_key is not None,
    reason="STRIPE_SECRET_KEY is set; bookkeeping-only payment tests are not applicable",
)


def _load_payload() -> dict:
    now = datetime.now(UTC)
    return {
        "title": "Phase 4 payment load",
        "weight_lbs": 2000,
        "pickup_address": "1 A St",
        "pickup_city": "Austin",
        "pickup_state": "TX",
        "pickup_zip": "78701",
        "pickup_window_start": (now + timedelta(days=1)).isoformat(),
        "pickup_window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        "dropoff_address": "2 B St",
        "dropoff_city": "Houston",
        "dropoff_state": "TX",
        "dropoff_zip": "77001",
        "dropoff_by": (now + timedelta(days=2)).isoformat(),
        "estimated_distance_miles": 200,
        "urgency": "standard",
    }


async def _signup(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "supersecret", "full_name": email.split("@")[0]},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


async def _enable_hauler(client: AsyncClient, headers: dict) -> None:
    r = await client.post(
        "/api/me/enable-hauler",
        json={"service_radius_miles": 25},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    r = await client.post(
        "/api/me/vehicles",
        json={"vehicle_type": "pickup", "max_payload_lbs": 5000, "is_default": True},
        headers=headers,
    )
    assert r.status_code == 201, r.text


async def _payment_for(load_id: str) -> Payment | None:
    async with AsyncSessionLocal() as db:
        return await db.scalar(
            select(Payment)
            .where(Payment.load_id == load_id)
            .order_by(Payment.created_at.desc())
        )


@pytest.fixture
async def actors(client: AsyncClient) -> dict[str, dict]:
    shipper = {"Authorization": f"Bearer {await _signup(client, 'shipper4@example.com')}"}
    hauler = {"Authorization": f"Bearer {await _signup(client, 'hauler4@example.com')}"}
    rando = {"Authorization": f"Bearer {await _signup(client, 'rando4@example.com')}"}
    await _enable_hauler(client, hauler)
    return {"shipper": shipper, "hauler": hauler, "rando": rando}


async def test_connect_onboarding_without_keys_returns_503(
    client: AsyncClient, actors: dict
) -> None:
    r = await client.post("/api/me/connect-onboarding", headers=actors["hauler"])
    assert r.status_code == 503, r.text
    assert "not configured" in r.json()["detail"]


async def test_connect_onboarding_by_non_hauler_forbidden(
    client: AsyncClient, actors: dict
) -> None:
    r = await client.post("/api/me/connect-onboarding", headers=actors["rando"])
    assert r.status_code == 403, r.text


async def test_payment_lifecycle_through_delivery(
    client: AsyncClient, actors: dict
) -> None:
    shipper_h, hauler_h, rando_h = actors["shipper"], actors["hauler"], actors["rando"]

    r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    load = r.json()
    load_id = load["id"]
    amount = load["calculated_price_cents"]
    expected_fee = calculate_platform_fee_cents(amount)
    expected_payout = amount - expected_fee

    # No payment yet
    r = await client.get(f"/api/loads/{load_id}/payment", headers=shipper_h)
    assert r.status_code == 404, r.text

    # Accept creates payment row (pending)
    r = await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)
    assert r.status_code == 200, r.text
    payment = await _payment_for(load_id)
    assert payment is not None
    assert payment.amount_cents == amount
    assert payment.platform_fee_cents == expected_fee
    assert payment.hauler_payout_cents == expected_payout
    assert payment.status.value == "pending"
    assert payment.stripe_payment_intent_id is None

    # Shipper & hauler can view, rando cannot
    r = await client.get(f"/api/loads/{load_id}/payment", headers=shipper_h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "pending"

    r = await client.get(f"/api/loads/{load_id}/payment", headers=hauler_h)
    assert r.status_code == 200, r.text

    r = await client.get(f"/api/loads/{load_id}/payment", headers=rando_h)
    assert r.status_code == 403, r.text

    # Walk to delivered
    await client.post(f"/api/loads/{load_id}/pickup", headers=hauler_h)
    await client.post(f"/api/loads/{load_id}/in-transit", headers=hauler_h)
    r = await client.post(f"/api/loads/{load_id}/deliver", headers=hauler_h)
    assert r.status_code == 200, r.text

    payment = await _payment_for(load_id)
    assert payment.status.value == "transferred"
    assert payment.captured_at is not None
    assert payment.transferred_at is not None


async def test_cancel_after_accept_refunds_payment(
    client: AsyncClient, actors: dict
) -> None:
    shipper_h, hauler_h = actors["shipper"], actors["hauler"]
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    ).json()["id"]
    await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)

    r = await client.post(
        f"/api/loads/{load_id}/cancel",
        json={"reason": "Shipper changed mind"},
        headers=shipper_h,
    )
    assert r.status_code == 200, r.text
    payment = await _payment_for(load_id)
    assert payment.status.value == "refunded"
    assert payment.refunded_at is not None


async def test_pre_accept_cancel_creates_no_payment(
    client: AsyncClient, actors: dict
) -> None:
    shipper_h = actors["shipper"]
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    ).json()["id"]

    r = await client.delete(f"/api/loads/{load_id}", headers=shipper_h)
    assert r.status_code == 204, r.text
    assert await _payment_for(load_id) is None


async def test_stripe_webhook_without_secret_returns_503(client: AsyncClient) -> None:
    r = await client.post(
        "/api/webhooks/stripe",
        headers={"Stripe-Signature": "t=1,v1=fake"},
        content=b"{}",
    )
    assert r.status_code == 503, r.text


async def test_stripe_webhook_without_signature_returns_400(client: AsyncClient) -> None:
    r = await client.post("/api/webhooks/stripe", content=b"{}")
    assert r.status_code == 400, r.text
