"""GET /api/loads/{id}/events — booking-event timeline endpoint."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


def _load_payload() -> dict:
    now = datetime.now(UTC)
    return {
        "title": "Events load",
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
    r = await client.post(
        "/api/me/vehicles",
        json={"vehicle_type": "pickup", "max_payload_lbs": 5000, "is_default": True},
        headers=headers,
    )
    assert r.status_code == 201, r.text


@pytest.fixture
async def actors(client: AsyncClient) -> dict[str, dict]:
    shipper = {"Authorization": f"Bearer {await _signup(client, 'shipper-ev@example.com')}"}
    hauler = {"Authorization": f"Bearer {await _signup(client, 'hauler-ev@example.com')}"}
    rando = {"Authorization": f"Bearer {await _signup(client, 'rando-ev@example.com')}"}
    await _enable_hauler(client, hauler)
    return {"shipper": shipper, "hauler": hauler, "rando": rando}


async def _create_load(client: AsyncClient, shipper_h: dict) -> str:
    r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_events_chronological_after_transitions(
    client: AsyncClient, actors: dict
) -> None:
    shipper_h, hauler_h = actors["shipper"], actors["hauler"]
    load_id = await _create_load(client, shipper_h)
    await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)
    await client.post(f"/api/loads/{load_id}/pickup", headers=hauler_h)
    await client.post(f"/api/loads/{load_id}/in-transit", headers=hauler_h)

    r = await client.get(f"/api/loads/{load_id}/events", headers=shipper_h)
    assert r.status_code == 200, r.text
    events = r.json()
    assert [e["event_type"] for e in events] == ["accepted", "picked_up", "in_transit"]

    first = events[0]
    assert first["load_id"] == load_id
    assert first["actor_user_id"] is not None
    assert first["created_at"] is not None
    assert isinstance(first["event_metadata"], dict)
    # Oldest first.
    timestamps = [e["created_at"] for e in events]
    assert timestamps == sorted(timestamps)


async def test_assigned_hauler_can_read_events(client: AsyncClient, actors: dict) -> None:
    shipper_h, hauler_h = actors["shipper"], actors["hauler"]
    load_id = await _create_load(client, shipper_h)
    await client.post(f"/api/loads/{load_id}/accept", headers=hauler_h)

    r = await client.get(f"/api/loads/{load_id}/events", headers=hauler_h)
    assert r.status_code == 200, r.text
    assert [e["event_type"] for e in r.json()] == ["accepted"]


async def test_unrelated_user_forbidden(client: AsyncClient, actors: dict) -> None:
    shipper_h, rando_h = actors["shipper"], actors["rando"]
    load_id = await _create_load(client, shipper_h)

    r = await client.get(f"/api/loads/{load_id}/events", headers=rando_h)
    assert r.status_code == 403, r.text


async def test_unknown_load_404(client: AsyncClient, actors: dict) -> None:
    r = await client.get("/api/loads/does-not-exist/events", headers=actors["shipper"])
    assert r.status_code == 404, r.text


async def test_posted_load_has_empty_timeline(client: AsyncClient, actors: dict) -> None:
    shipper_h = actors["shipper"]
    load_id = await _create_load(client, shipper_h)

    r = await client.get(f"/api/loads/{load_id}/events", headers=shipper_h)
    assert r.status_code == 200, r.text
    assert r.json() == []
