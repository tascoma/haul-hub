"""Booking lifecycle: accept → pickup → in_transit → delivered, plus cancel paths
(formerly scripts/smoke_phase3.py)."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.databases import AsyncSessionLocal
from app.models.booking_event import BookingEvent


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
        json={"service_radius_miles": 50},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    # The operational profile lives separately from the truck; add a default vehicle.
    r = await client.post(
        "/api/me/vehicles",
        json={"vehicle_type": "pickup", "max_payload_lbs": 5000, "is_default": True},
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


@pytest.fixture
async def actors(client: AsyncClient) -> dict[str, dict]:
    shipper = {"Authorization": f"Bearer {await _signup(client, 'shipper3@example.com')}"}
    hauler = {"Authorization": f"Bearer {await _signup(client, 'hauler3@example.com')}"}
    rando = {"Authorization": f"Bearer {await _signup(client, 'rando3@example.com')}"}
    await _enable_hauler(client, hauler)
    return {"shipper": shipper, "hauler": hauler, "rando": rando}


async def _create_load(client: AsyncClient, shipper_h: dict) -> str:
    r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    return r.json()["id"]


async def test_happy_path_full_lifecycle(client: AsyncClient, actors: dict) -> None:
    shipper_h, hauler_h, rando_h = actors["shipper"], actors["hauler"], actors["rando"]
    load_id = await _create_load(client, shipper_h)

    # Non-hauler can't accept
    r = await client.post(f"/api/loads/{load_id}/accept", headers=rando_h)
    assert r.status_code == 403, r.text

    # Shipper can't accept own load
    r = await client.post(f"/api/loads/{load_id}/accept", headers=shipper_h)
    assert r.status_code == 403, r.text

    # Hauler accepts
    r = await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "accepted"
    assert body["hauler_id"] is not None
    assert body["accepted_at"] is not None

    # Re-accept
    r = await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)
    assert r.status_code == 409, r.text

    # Skip-state deliver
    r = await client.post(f"/api/loads/{load_id}/deliver", headers=hauler_h)
    assert r.status_code == 409, r.text

    # Wrong hauler pickup
    r = await client.post(f"/api/loads/{load_id}/pickup", headers=rando_h)
    assert r.status_code == 403, r.text

    # Pickup
    r = await client.post(f"/api/loads/{load_id}/pickup", headers=hauler_h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "picked_up"
    assert r.json()["picked_up_at"] is not None

    # In transit
    r = await client.post(f"/api/loads/{load_id}/in-transit", headers=hauler_h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "in_transit"

    # Deliver
    r = await client.post(f"/api/loads/{load_id}/deliver", headers=hauler_h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "delivered"
    assert r.json()["delivered_at"] is not None

    # Cancel delivered (terminal)
    r = await client.post(f"/api/loads/{load_id}/cancel", headers=shipper_h)
    assert r.status_code == 409, r.text

    events = await _events_for(load_id)
    assert [e.event_type.value for e in events] == [
        "accepted",
        "picked_up",
        "in_transit",
        "delivered",
    ]


async def test_cancel_after_accept_by_shipper(client: AsyncClient, actors: dict) -> None:
    shipper_h, hauler_h = actors["shipper"], actors["hauler"]
    load_id = await _create_load(client, shipper_h)
    await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)

    r = await client.post(
        f"/api/loads/{load_id}/cancel",
        json={"reason": "Customer changed plans"},
        headers=shipper_h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"

    events = await _events_for(load_id)
    cancel_evt = events[-1]
    assert cancel_evt.event_type.value == "cancelled"
    assert cancel_evt.event_metadata == {
        "actor_role": "shipper",
        "reason": "Customer changed plans",
    }


async def test_cancel_after_accept_by_hauler(client: AsyncClient, actors: dict) -> None:
    shipper_h, hauler_h = actors["shipper"], actors["hauler"]
    load_id = await _create_load(client, shipper_h)
    await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)

    r = await client.post(
        f"/api/loads/{load_id}/cancel",
        json={"reason": "Truck broke down"},
        headers=hauler_h,
    )
    assert r.status_code == 200, r.text
    events = await _events_for(load_id)
    assert events[-1].event_metadata["actor_role"] == "hauler"


async def test_random_user_cannot_cancel(client: AsyncClient, actors: dict) -> None:
    shipper_h, hauler_h, rando_h = actors["shipper"], actors["hauler"], actors["rando"]
    load_id = await _create_load(client, shipper_h)
    await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)

    r = await client.post(f"/api/loads/{load_id}/cancel", headers=rando_h)
    assert r.status_code == 403, r.text


async def test_delete_pre_acceptance_writes_audit_event(
    client: AsyncClient, actors: dict
) -> None:
    shipper_h = actors["shipper"]
    load_id = await _create_load(client, shipper_h)

    r = await client.delete(f"/api/loads/{load_id}", headers=shipper_h)
    assert r.status_code == 204, r.text

    events = await _events_for(load_id)
    assert [e.event_type.value for e in events] == ["cancelled"]


async def test_delete_post_acceptance_409_with_hint(
    client: AsyncClient, actors: dict
) -> None:
    shipper_h, hauler_h = actors["shipper"], actors["hauler"]
    load_id = await _create_load(client, shipper_h)
    await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)

    r = await client.delete(f"/api/loads/{load_id}", headers=shipper_h)
    assert r.status_code == 409, r.text
    assert "POST /cancel" in r.json()["detail"]
