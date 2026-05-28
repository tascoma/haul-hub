"""Loads CRUD + pricing + photo upload (formerly scripts/smoke_phase2.py)."""

import io
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models.load import Urgency
from app.services.pricing import calculate_price_cents


def _load_payload(suffix: str = "") -> dict:
    now = datetime.now(UTC)
    return {
        "title": f"Pallet of stuff{suffix}",
        "description": "Three pallets, palletized",
        "weight_lbs": 1500,
        "length_ft": 8,
        "width_ft": 4,
        "height_ft": 4,
        "pickup_address": "123 Main St",
        "pickup_city": "Austin",
        "pickup_state": "TX",
        "pickup_zip": "78701",
        "pickup_window_start": (now + timedelta(days=1)).isoformat(),
        "pickup_window_end": (now + timedelta(days=1, hours=4)).isoformat(),
        "dropoff_address": "456 Elm St",
        "dropoff_city": "Dallas",
        "dropoff_state": "TX",
        "dropoff_zip": "75201",
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


@pytest.fixture
async def shipper_h(client: AsyncClient) -> dict:
    token = await _signup(client, "shipper@example.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def other_h(client: AsyncClient) -> dict:
    token = await _signup(client, "other@example.com")
    return {"Authorization": f"Bearer {token}"}


def test_pricing_formula_reference() -> None:
    expected = calculate_price_cents(
        distance_miles=200, weight_lbs=1500, urgency=Urgency.standard
    )
    assert expected == (
        settings.price_base_cents
        + settings.price_per_mile_cents * 200
        + settings.price_weight_surcharge_per_100lb_cents * 15
    )


async def test_create_load_uses_calculated_price(
    client: AsyncClient, shipper_h: dict
) -> None:
    expected = calculate_price_cents(
        distance_miles=200, weight_lbs=1500, urgency=Urgency.standard
    )
    r = await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    assert r.status_code == 201, r.text
    load = r.json()
    assert load["status"] == "posted"
    assert load["calculated_price_cents"] == expected


async def test_express_price_higher_than_standard(
    client: AsyncClient, shipper_h: dict
) -> None:
    std = (await client.post("/api/loads", json=_load_payload(), headers=shipper_h)).json()
    express = (
        await client.post(
            "/api/loads",
            json=_load_payload(" (express)") | {"urgency": "express"},
            headers=shipper_h,
        )
    ).json()
    assert express["calculated_price_cents"] > std["calculated_price_cents"]
    assert express["calculated_price_cents"] == int(
        round(std["calculated_price_cents"] * settings.price_express_multiplier)
    )


async def test_browse_and_filter_loads(
    client: AsyncClient, shipper_h: dict, other_h: dict
) -> None:
    await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    await client.post(
        "/api/loads", json=_load_payload(" (express)") | {"urgency": "express"}, headers=shipper_h
    )

    r = await client.get("/api/loads", headers=other_h)
    assert r.status_code == 200, r.text
    assert len(r.json()) >= 2

    r = await client.get("/api/loads?city=Austin", headers=other_h)
    assert r.status_code == 200, r.text
    assert all(l["pickup_city"] == "Austin" for l in r.json())

    r = await client.get("/api/loads?city=Nowhere", headers=other_h)
    assert r.json() == []


async def test_get_load_detail(client: AsyncClient, shipper_h: dict, other_h: dict) -> None:
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    ).json()["id"]
    r = await client.get(f"/api/loads/{load_id}", headers=other_h)
    assert r.status_code == 200, r.text


async def test_patch_load_recalculates_price(
    client: AsyncClient, shipper_h: dict
) -> None:
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    ).json()["id"]
    r = await client.patch(
        f"/api/loads/{load_id}",
        json={"weight_lbs": 3000, "title": "Bigger pallet"},
        headers=shipper_h,
    )
    assert r.status_code == 200, r.text
    updated = r.json()
    recalc = calculate_price_cents(
        distance_miles=200, weight_lbs=3000, urgency=Urgency.standard
    )
    assert updated["weight_lbs"] == 3000
    assert updated["title"] == "Bigger pallet"
    assert updated["calculated_price_cents"] == recalc


async def test_patch_by_non_owner_forbidden(
    client: AsyncClient, shipper_h: dict, other_h: dict
) -> None:
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    ).json()["id"]
    r = await client.patch(
        f"/api/loads/{load_id}", json={"title": "nope"}, headers=other_h
    )
    assert r.status_code == 403, r.text


async def test_photo_upload_and_serve(
    client: AsyncClient, shipper_h: dict, other_h: dict
) -> None:
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    ).json()["id"]

    files = {"file": ("test.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake"), "image/png")}
    r = await client.post(f"/api/loads/{load_id}/photos", files=files, headers=shipper_h)
    assert r.status_code == 200, r.text
    photo_url = r.json()["photo_urls"][0]
    assert photo_url.startswith("/uploads/loads/")

    r = await client.get(photo_url)
    assert r.status_code == 200, r.text
    assert r.content.startswith(b"\x89PNG")

    # Non-owner can't upload
    files = {"file": ("nope.png", io.BytesIO(b"x"), "image/png")}
    r = await client.post(f"/api/loads/{load_id}/photos", files=files, headers=other_h)
    assert r.status_code == 403, r.text


async def test_delete_load_lifecycle(
    client: AsyncClient, shipper_h: dict, other_h: dict
) -> None:
    load_id = (
        await client.post("/api/loads", json=_load_payload(), headers=shipper_h)
    ).json()["id"]

    # Non-owner cancel
    r = await client.delete(f"/api/loads/{load_id}", headers=other_h)
    assert r.status_code == 403, r.text

    # Owner cancel
    r = await client.delete(f"/api/loads/{load_id}", headers=shipper_h)
    assert r.status_code == 204, r.text

    r = await client.get(f"/api/loads/{load_id}", headers=shipper_h)
    body = r.json()
    assert body["status"] == "cancelled"
    assert body["cancelled_at"] is not None

    # Re-delete
    r = await client.delete(f"/api/loads/{load_id}", headers=shipper_h)
    assert r.status_code == 409, r.text

    # Cancelled loads excluded from browse
    r = await client.get("/api/loads", headers=other_h)
    assert load_id not in [l["id"] for l in r.json()]


async def test_invalid_payloads_return_422(
    client: AsyncClient, shipper_h: dict
) -> None:
    r = await client.post("/api/loads", json={"title": "x"}, headers=shipper_h)
    assert r.status_code == 422

    bad = _load_payload() | {
        "pickup_window_end": (datetime.now(UTC) - timedelta(days=10)).isoformat()
    }
    r = await client.post("/api/loads", json=bad, headers=shipper_h)
    assert r.status_code == 422, r.text


async def test_near_me_filters_to_service_radius(
    client: AsyncClient, shipper_h: dict
) -> None:
    """near_me=true keeps only loads whose pickup is within the hauler's radius."""
    from sqlalchemy import select

    from app.databases import AsyncSessionLocal
    from app.models.address import Address
    from app.models.user import HaulerProfile

    # Two posted loads with distinct pickup cities → distinct address rows.
    near = _load_payload(" near") | {"pickup_city": "Rogers", "pickup_state": "AR", "pickup_zip": "72756"}
    far = _load_payload(" far") | {"pickup_city": "Dallas", "pickup_state": "TX", "pickup_zip": "75201"}
    near_id = (await client.post("/api/loads", json=near, headers=shipper_h)).json()["id"]
    far_id = (await client.post("/api/loads", json=far, headers=shipper_h)).json()["id"]

    # A hauler with a 50-mi radius based in Bentonville, AR.
    hauler_h = await _signup_hauler(client, "hank@example.com")
    await client.post(
        "/api/me/enable-hauler",
        json={"company_name": "Ozark Haul Co", "service_radius_miles": 50},
        headers=hauler_h,
    )

    # Set coordinates directly so the radius math is deterministic regardless
    # of whether geocoding is configured in the test environment.
    async with AsyncSessionLocal() as db:
        home = Address(line1="1108 SW 14th St", city="Bentonville", state="AR",
                       postal_code="72712", lat=36.3551, lng=-94.2305)
        db.add(home)
        await db.flush()
        rogers = await db.scalar(select(Address).where(Address.city == "Rogers"))
        dallas = await db.scalar(select(Address).where(Address.city == "Dallas"))
        rogers.lat, rogers.lng = 36.3340, -94.1455   # ~8 mi from Bentonville
        dallas.lat, dallas.lng = 32.7795, -96.8076    # ~330 mi away
        profile = await db.scalar(select(HaulerProfile))
        profile.home_base_address_id = home.id
        await db.commit()

    in_radius = await client.get("/api/loads?near_me=true", headers=hauler_h)
    ids = [l["id"] for l in in_radius.json()]
    assert near_id in ids
    assert far_id not in ids

    # Without the filter, both are visible.
    all_ids = [l["id"] for l in (await client.get("/api/loads", headers=hauler_h)).json()]
    assert {near_id, far_id} <= set(all_ids)


async def _signup_hauler(client: AsyncClient, email: str) -> dict:
    r = await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "supersecret", "full_name": "Hank", "roles": ["hauler"]},
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
