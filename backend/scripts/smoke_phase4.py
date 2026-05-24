"""Smoke test for Phase 4 payments (bookkeeping-only mode, no STRIPE_SECRET_KEY).

Verifies that Payment rows are correctly created, computed, and transitioned through
the booking lifecycle even with Stripe disabled. Real Stripe API integration is tested
separately when STRIPE_SECRET_KEY=sk_test_... is set.

Run from backend/:
    uv run python scripts/smoke_phase4.py
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.databases import AsyncSessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.payment import Payment  # noqa: E402
from app.services.payments import calculate_platform_fee_cents  # noqa: E402


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
        json={"vehicle_type": "pickup", "max_weight_lbs": 5000},
        headers=headers,
    )
    assert r.status_code == 201, r.text


async def _payment_for(load_id: str) -> Payment | None:
    async with AsyncSessionLocal() as db:
        return await db.scalar(
            select(Payment).where(Payment.load_id == load_id).order_by(Payment.created_at.desc())
        )


async def main() -> None:
    assert settings.stripe_secret_key is None, (
        "STRIPE_SECRET_KEY is set; this smoke test expects bookkeeping-only mode. "
        "Unset it before running, or write a separate test for the real Stripe path."
    )
    print(f"running in bookkeeping-only mode (platform fee = {settings.platform_fee_bps} bps)")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        shipper_token = await _signup(client, "shipper4@example.com")
        hauler_token = await _signup(client, "hauler4@example.com")
        rando_token = await _signup(client, "rando4@example.com")
        shipper_h = {"Authorization": f"Bearer {shipper_token}"}
        hauler_h = {"Authorization": f"Bearer {hauler_token}"}
        rando_h = {"Authorization": f"Bearer {rando_token}"}
        await _enable_hauler(client, hauler_h)

        # Onboarding without Stripe configured → 503
        r = await client.post("/api/me/connect-onboarding", headers=hauler_h)
        assert r.status_code == 503, r.text
        assert "not configured" in r.json()["detail"]
        print("connect-onboarding without keys -> 503 ok")

        # Non-hauler can't onboard
        r = await client.post("/api/me/connect-onboarding", headers=rando_h)
        assert r.status_code == 403, r.text
        print("connect-onboarding by non-hauler -> 403 ok")

        # === Happy path: accept → deliver, payment row gets created + transferred ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load = r.json()
        load_id = load["id"]
        amount = load["calculated_price_cents"]
        expected_fee = calculate_platform_fee_cents(amount)
        expected_payout = amount - expected_fee
        print(f"load {load_id[:8]}: amount={amount} fee={expected_fee} payout={expected_payout}")

        # No payment yet
        r = await client.get(f"/api/loads/{load_id}/payment", headers=shipper_h)
        assert r.status_code == 404, r.text
        print("no payment before accept -> 404 ok")

        # Hauler accepts → payment row created (status=pending)
        r = await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)
        assert r.status_code == 200, r.text
        payment = await _payment_for(load_id)
        assert payment is not None
        assert payment.amount_cents == amount
        assert payment.platform_fee_cents == expected_fee
        assert payment.hauler_payout_cents == expected_payout
        assert payment.status.value == "pending"
        assert payment.stripe_payment_intent_id is None
        print(f"accept -> payment row created, status={payment.status.value}")

        # Shipper can view payment
        r = await client.get(f"/api/loads/{load_id}/payment", headers=shipper_h)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "pending"
        print("shipper GET payment ok")

        # Hauler can view payment
        r = await client.get(f"/api/loads/{load_id}/payment", headers=hauler_h)
        assert r.status_code == 200, r.text
        print("hauler GET payment ok")

        # Random user cannot
        r = await client.get(f"/api/loads/{load_id}/payment", headers=rando_h)
        assert r.status_code == 403, r.text
        print("rando GET payment -> 403 ok")

        # Walk to delivered
        await client.post(f"/api/loads/{load_id}/pickup", headers=hauler_h)
        await client.post(f"/api/loads/{load_id}/in-transit", headers=hauler_h)
        r = await client.post(f"/api/loads/{load_id}/deliver", headers=hauler_h)
        assert r.status_code == 200, r.text

        payment = await _payment_for(load_id)
        assert payment.status.value == "transferred", payment.status
        assert payment.captured_at is not None
        assert payment.transferred_at is not None
        print(f"deliver -> payment status={payment.status.value} (captured_at + transferred_at set)")

        # === Cancel-after-accept triggers refund bookkeeping ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load2_id = r.json()["id"]
        await client.post(f"/api/loads/{load2_id}/accept", headers=hauler_h)
        r = await client.post(
            f"/api/loads/{load2_id}/cancel",
            json={"reason": "Shipper changed mind"},
            headers=shipper_h,
        )
        assert r.status_code == 200, r.text
        payment2 = await _payment_for(load2_id)
        assert payment2.status.value == "refunded", payment2.status
        assert payment2.refunded_at is not None
        print(f"cancel after accept -> payment.status={payment2.status.value}, refunded_at set")

        # === Pre-acceptance cancel: no payment row exists, cancel is a no-op for payments ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load3_id = r.json()["id"]
        r = await client.delete(f"/api/loads/{load3_id}", headers=shipper_h)
        assert r.status_code == 204, r.text
        assert await _payment_for(load3_id) is None
        print("pre-accept cancel: no payment row created ok")

        # === Stripe webhook without secret configured → 503 ===
        r = await client.post(
            "/api/webhooks/stripe",
            headers={"Stripe-Signature": "t=1,v1=fake"},
            content=b"{}",
        )
        assert r.status_code == 503, r.text
        print("webhook without secret -> 503 ok")

        # Missing signature header → 400
        r = await client.post("/api/webhooks/stripe", content=b"{}")
        assert r.status_code == 400, r.text
        print("webhook without signature header -> 400 ok")

    print("\nAll Phase 4 checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
