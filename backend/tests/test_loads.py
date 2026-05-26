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
