"""Smoke test for Phase 3 booking lifecycle. Run from backend/:
    uv run python scripts/smoke_phase3.py
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.databases import AsyncSessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.booking_event import BookingEvent  # noqa: E402


def _load_payload() -> dict:
    now = datetime.now(UTC)
    return {
        "title": "Lifecycle load",
        "weight_lbs": 1000,
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
        "estimated_distance_miles": 165,
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


async def _events_for(load_id: str) -> list[BookingEvent]:
    async with AsyncSessionLocal() as db:
        result = await db.scalars(
            select(BookingEvent)
            .where(BookingEvent.load_id == load_id)
            .order_by(BookingEvent.created_at)
        )
        return list(result)


async def main() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        shipper_token = await _signup(client, "shipper3@example.com")
        hauler_token = await _signup(client, "hauler3@example.com")
        rando_token = await _signup(client, "rando3@example.com")
        shipper_h = {"Authorization": f"Bearer {shipper_token}"}
        hauler_h = {"Authorization": f"Bearer {hauler_token}"}
        rando_h = {"Authorization": f"Bearer {rando_token}"}

        await _enable_hauler(client, hauler_h)
        print("hauler enabled")

        # === Happy path: posted → accepted → picked_up → in_transit → delivered ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load_id = r.json()["id"]
        print(f"created load {load_id}")

        # Non-hauler can't accept (rando never enabled hauler role)
        r = await client.post(f"/api/loads/{load_id}/accept", headers=rando_h)
        assert r.status_code == 403, r.text
        print("non-hauler accept -> 403 ok")

        # Shipper can't accept their own load
        r = await client.post(f"/api/loads/{load_id}/accept", headers=shipper_h)
        assert r.status_code == 403, r.text
        print("shipper accept own load -> 403 ok")

        # Hauler accepts
        r = await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "accepted"
        assert body["hauler_id"] is not None
        assert body["accepted_at"] is not None
        print("accept ok")

        # Re-accept (now in 'accepted') → 409
        r = await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)
        assert r.status_code == 409, r.text
        print("re-accept -> 409 ok")

        # Invalid order: deliver before pickup → 409
        r = await client.post(f"/api/loads/{load_id}/deliver", headers=hauler_h)
        assert r.status_code == 409, r.text
        print("skip-state deliver -> 409 ok")

        # Wrong hauler tries pickup → 403 (rando is not the assigned hauler)
        r = await client.post(f"/api/loads/{load_id}/pickup", headers=rando_h)
        assert r.status_code == 403, r.text
        print("non-assigned hauler pickup -> 403 ok")

        # Pickup
        r = await client.post(f"/api/loads/{load_id}/pickup", headers=hauler_h)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "picked_up"
        assert r.json()["picked_up_at"] is not None
        print("pickup ok")

        # In transit
        r = await client.post(f"/api/loads/{load_id}/in-transit", headers=hauler_h)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "in_transit"
        print("in-transit ok")

        # Deliver
        r = await client.post(f"/api/loads/{load_id}/deliver", headers=hauler_h)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "delivered"
        assert r.json()["delivered_at"] is not None
        print("deliver ok")

        # Cancel delivered load → 409 (terminal)
        r = await client.post(f"/api/loads/{load_id}/cancel", headers=shipper_h)
        assert r.status_code == 409, r.text
        print("cancel delivered -> 409 ok")

        # Verify audit trail
        events = await _events_for(load_id)
        kinds = [e.event_type.value for e in events]
        assert kinds == ["accepted", "picked_up", "in_transit", "delivered"], kinds
        print(f"audit trail ok: {kinds}")

        # === Cancel-by-shipper after acceptance ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load2 = r.json()["id"]
        await client.post(f"/api/loads/{load2}/accept", headers=hauler_h)
        r = await client.post(
            f"/api/loads/{load2}/cancel",
            json={"reason": "Customer changed plans"},
            headers=shipper_h,
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "cancelled"
        events = await _events_for(load2)
        cancel_evt = events[-1]
        assert cancel_evt.event_type.value == "cancelled"
        assert cancel_evt.event_metadata == {
            "actor_role": "shipper",
            "reason": "Customer changed plans",
        }
        print("post-accept cancel by shipper ok, metadata recorded")

        # === Cancel-by-hauler after acceptance ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load3 = r.json()["id"]
        await client.post(f"/api/loads/{load3}/accept", headers=hauler_h)
        r = await client.post(
            f"/api/loads/{load3}/cancel", json={"reason": "Truck broke down"}, headers=hauler_h
        )
        assert r.status_code == 200, r.text
        events = await _events_for(load3)
        assert events[-1].event_metadata["actor_role"] == "hauler"
        print("post-accept cancel by hauler ok")

        # === Random user can't cancel ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load4 = r.json()["id"]
        await client.post(f"/api/loads/{load4}/accept", headers=hauler_h)
        r = await client.post(f"/api/loads/{load4}/cancel", headers=rando_h)
        assert r.status_code == 403, r.text
        print("rando cancel -> 403 ok")

        # === DELETE pre-acceptance still works, writes audit event ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load5 = r.json()["id"]
        r = await client.delete(f"/api/loads/{load5}", headers=shipper_h)
        assert r.status_code == 204, r.text
        events = await _events_for(load5)
        assert [e.event_type.value for e in events] == ["cancelled"]
        print("DELETE pre-accept writes audit event ok")

        # === DELETE post-acceptance → 409, points caller to POST /cancel ===
        r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
        load6 = r.json()["id"]
        await client.post(f"/api/loads/{load6}/accept", headers=hauler_h)
        r = await client.delete(f"/api/loads/{load6}", headers=shipper_h)
        assert r.status_code == 409, r.text
        assert "POST /cancel" in r.json()["detail"]
        print("DELETE post-accept -> 409 with hint ok")

    print("\nAll Phase 3 checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
