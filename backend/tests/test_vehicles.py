"""Vehicles table — CRUD + the partial-unique default-vehicle index."""

import pytest
from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "supersecret", "full_name": email.split("@")[0]},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


@pytest.fixture
async def hauler_h(client: AsyncClient) -> dict:
    token = await _signup(client, "veh@example.com")
    h = {"Authorization": f"Bearer {token}"}
    r = await client.post("/api/me/enable-hauler", json={}, headers=h)
    assert r.status_code == 201, r.text
    return h


async def test_create_and_list_vehicles(client: AsyncClient, hauler_h: dict) -> None:
    r = await client.post(
        "/api/me/vehicles",
        json={
            "vehicle_type": "box_truck",
            "make": "Isuzu",
            "model": "NPR",
            "max_payload_lbs": 12000,
            "is_default": True,
        },
        headers=hauler_h,
    )
    assert r.status_code == 201, r.text
    assert r.json()["vehicle_type"] == "box_truck"
    assert r.json()["is_default"] is True

    r = await client.get("/api/me/vehicles", headers=hauler_h)
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1


async def test_second_default_flips_previous(client: AsyncClient, hauler_h: dict) -> None:
    v1 = (
        await client.post(
            "/api/me/vehicles",
            json={"vehicle_type": "pickup", "is_default": True},
            headers=hauler_h,
        )
    ).json()
    v2 = (
        await client.post(
            "/api/me/vehicles",
            json={"vehicle_type": "flatbed", "is_default": True},
            headers=hauler_h,
        )
    ).json()
    assert v2["is_default"] is True

    listed = (await client.get("/api/me/vehicles", headers=hauler_h)).json()
    defaults = [v for v in listed if v["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == v2["id"]
    # v1 still exists but is no longer default.
    assert any(v["id"] == v1["id"] and not v["is_default"] for v in listed)


async def test_delete_retires_vehicle(client: AsyncClient, hauler_h: dict) -> None:
    v = (
        await client.post(
            "/api/me/vehicles",
            json={"vehicle_type": "pickup", "is_default": True},
            headers=hauler_h,
        )
    ).json()
    r = await client.delete(f"/api/me/vehicles/{v['id']}", headers=hauler_h)
    assert r.status_code == 204, r.text

    listed = (await client.get("/api/me/vehicles", headers=hauler_h)).json()
    assert listed[0]["status"] == "retired"
    assert listed[0]["is_default"] is False
