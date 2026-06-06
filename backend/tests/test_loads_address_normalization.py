"""Loads address dual-write — flat columns and FK kept in sync."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


def _payload() -> dict:
    now = datetime.now(UTC)
    return {
        "title": "Normalize test",
        "weight_lbs": 500,
        "pickup_address": "1 Pickup Ln",
        "pickup_city": "Austin",
        "pickup_state": "TX",
        "pickup_zip": "78701",
        "pickup_window_start": (now + timedelta(days=1)).isoformat(),
        "pickup_window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        "dropoff_address": "1 Dropoff Ln",
        "dropoff_city": "Dallas",
        "dropoff_state": "TX",
        "dropoff_zip": "75201",
        "dropoff_by": (now + timedelta(days=2)).isoformat(),
        "estimated_distance_miles": 200,
        "urgency": "standard",
    }


async def _signup(client: AsyncClient, email: str) -> dict:
    r = await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "supersecret", "full_name": email.split("@")[0]},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_post_load_fills_both_flat_and_fk(client: AsyncClient) -> None:
    auth = await _signup(client, "norm@example.com")
    r = await client.post("/api/loads", json=_payload(), headers=auth)
    assert r.status_code == 201, r.text
    body = r.json()

    # Flat columns intact (frontend compatibility).
    assert body["pickup_city"] == "Austin"
    assert body["dropoff_zip"] == "75201"

    # FK columns populated.
    assert body["pickup_address_id"]
    assert body["dropoff_address_id"]
    assert body["pickup_address_id"] != body["dropoff_address_id"]

    # Nested address objects returned for new clients.
    assert body["pickup_address_ref"]["line1"] == "1 Pickup Ln"
    assert body["dropoff_address_ref"]["postal_code"] == "75201"

    # Reference code generated.
    assert body["reference_code"].startswith("HH-")
    assert len(body["reference_code"]) == 11  # "HH-" + 8 chars


async def test_patch_pickup_fields_realigns_fk(client: AsyncClient) -> None:
    auth = await _signup(client, "patch@example.com")
    load = (await client.post("/api/loads", json=_payload(), headers=auth)).json()
    original_pickup_id = load["pickup_address_id"]

    r = await client.patch(
        f"/api/loads/{load['id']}",
        json={"pickup_address": "999 New Way", "pickup_zip": "78702"},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pickup_address"] == "999 New Way"
    assert body["pickup_address_id"] != original_pickup_id
    assert body["pickup_address_ref"]["line1"] == "999 New Way"
    # Dropoff FK untouched.
    assert body["dropoff_address_id"] == load["dropoff_address_id"]


async def test_reference_codes_are_unique_across_loads(client: AsyncClient) -> None:
    auth = await _signup(client, "ref@example.com")
    codes = set()
    for _ in range(5):
        body = (await client.post("/api/loads", json=_payload(), headers=auth)).json()
        codes.add(body["reference_code"])
    assert len(codes) == 5
