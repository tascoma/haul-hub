"""Addresses table + saved address book + find_or_create dedup behavior.

Note: the PostGIS `geom` column and its trigger are Postgres-only and exercised
in production by migration 0008; they aren't tested here because the test suite
runs against SQLite.
"""

from httpx import AsyncClient
from sqlalchemy import text

from app.databases import AsyncSessionLocal


async def _signup(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "supersecret", "full_name": email.split("@")[0]},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


async def test_create_address_round_trips_fields(client: AsyncClient) -> None:
    token = await _signup(client, "addr@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/me/addresses/raw",
        json={
            "line1": "1 Market St",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "lat": "37.794500",
            "lng": "-122.394700",
            "address_type_hint": "commercial",
        },
        headers=auth,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["line1"] == "1 Market St"
    assert body["city"] == "San Francisco"
    assert body["address_type_hint"] == "commercial"
    assert body["lat"] == "37.794500"
    assert body["lng"] == "-122.394700"


async def test_save_address_to_book_enforces_one_default(client: AsyncClient) -> None:
    token = await _signup(client, "book@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    a1 = (
        await client.post(
            "/api/me/addresses/raw",
            json={"line1": "1 A", "city": "X", "state": "TX", "postal_code": "00001"},
            headers=auth,
        )
    ).json()["id"]
    a2 = (
        await client.post(
            "/api/me/addresses/raw",
            json={"line1": "2 B", "city": "Y", "state": "TX", "postal_code": "00002"},
            headers=auth,
        )
    ).json()["id"]

    r = await client.post(
        "/api/me/addresses",
        json={"address_id": a1, "label": "Home", "is_default_pickup": True},
        headers=auth,
    )
    assert r.status_code == 201, r.text

    # Saving a second default-pickup should flip the previous one off, not 409.
    r = await client.post(
        "/api/me/addresses",
        json={"address_id": a2, "label": "Office", "is_default_pickup": True},
        headers=auth,
    )
    assert r.status_code == 201, r.text

    r = await client.get("/api/me/addresses", headers=auth)
    defaults = [s for s in r.json() if s["is_default_pickup"]]
    assert len(defaults) == 1
    assert defaults[0]["address_id"] == a2


async def test_find_or_create_dedupes_on_canonical_key(client: AsyncClient) -> None:
    """Posting two loads with identical pickup details reuses one addresses row."""
    token = await _signup(client, "dedupe@example.com")
    auth = {"Authorization": f"Bearer {token}"}

    payload = {
        "title": "Test load",
        "weight_lbs": 100,
        "pickup_address": "123 Same St",
        "pickup_city": "Austin",
        "pickup_state": "TX",
        "pickup_zip": "78701",
        "pickup_window_start": "2026-06-01T10:00:00Z",
        "pickup_window_end": "2026-06-01T14:00:00Z",
        "dropoff_address": "456 Different Way",
        "dropoff_city": "Dallas",
        "dropoff_state": "TX",
        "dropoff_zip": "75201",
        "dropoff_by": "2026-06-02T10:00:00Z",
        "estimated_distance_miles": 200,
        "urgency": "standard",
    }

    l1 = (await client.post("/api/loads", json=payload, headers=auth)).json()
    l2 = (await client.post("/api/loads", json=payload, headers=auth)).json()

    assert l1["pickup_address_id"] == l2["pickup_address_id"]
    assert l1["dropoff_address_id"] == l2["dropoff_address_id"]

    async with AsyncSessionLocal() as db:
        count = (await db.execute(text("SELECT COUNT(*) FROM addresses"))).scalar_one()
    assert count == 2
