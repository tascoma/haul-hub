"""Auth + profile endpoints (formerly scripts/smoke_phase1.py)."""

from httpx import AsyncClient


async def test_signup_login_and_profile_flow(client: AsyncClient) -> None:
    r = await client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "supersecret", "full_name": "Alice"},
    )
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    assert token

    # Duplicate signup
    r = await client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "supersecret"},
    )
    assert r.status_code == 409, r.text

    # Login
    r = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "supersecret"},
    )
    assert r.status_code == 200, r.text

    # GET /api/me
    r = await client.get("/api/me", headers=auth)
    assert r.status_code == 200, r.text
    me = r.json()
    assert me["email"] == "alice@example.com"
    assert me["profile"]["shipper_enabled"] is True
    assert me["profile"]["hauler_enabled"] is False

    # PATCH /api/me
    r = await client.patch("/api/me", json={"phone": "+15551234567"}, headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["profile"]["phone"] == "+15551234567"

    # Hauler profile not yet enabled
    r = await client.get("/api/me/hauler-profile", headers=auth)
    assert r.status_code == 404, r.text

    # Enable hauler
    r = await client.post(
        "/api/me/enable-hauler",
        json={"company_name": "Alice Hauling LLC", "business_type": "llc", "service_radius_miles": 50},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["company_name"] == "Alice Hauling LLC"
    assert r.json()["business_type"] == "llc"

    # Now hauler-enabled
    r = await client.get("/api/me", headers=auth)
    assert r.json()["profile"]["hauler_enabled"] is True

    # GET hauler profile
    r = await client.get("/api/me/hauler-profile", headers=auth)
    assert r.status_code == 200, r.text
    assert r.json()["service_radius_miles"] == 50

    # Add a vehicle separately (replaces old in-profile vehicle fields)
    r = await client.post(
        "/api/me/vehicles",
        json={"vehicle_type": "pickup_with_trailer", "max_payload_lbs": 10000, "is_default": True},
        headers=auth,
    )
    assert r.status_code == 201, r.text
    assert r.json()["vehicle_type"] == "pickup_with_trailer"
    assert r.json()["max_payload_lbs"] == 10000

    # Enabling again is idempotent — returns existing profile with 200
    r = await client.post(
        "/api/me/enable-hauler",
        json={"company_name": "duplicate"},
        headers=auth,
    )
    assert r.status_code == 200, r.text
    assert r.json()["company_name"] == "Alice Hauling LLC"  # unchanged


async def test_me_requires_valid_token(client: AsyncClient) -> None:
    r = await client.get("/api/me")
    assert r.status_code == 401, r.text

    r = await client.get("/api/me", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401, r.text


async def test_change_password(client: AsyncClient) -> None:
    # Sign up
    r = await client.post(
        "/api/auth/signup",
        json={"email": "bob@example.com", "password": "OldPass1!", "full_name": "Bob"},
    )
    assert r.status_code == 201, r.text
    auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    # Wrong current password is rejected
    r = await client.patch(
        "/api/me/password",
        json={"current_password": "WrongPass!", "new_password": "NewPass1!"},
        headers=auth,
    )
    assert r.status_code == 400, r.text

    # Correct change succeeds
    r = await client.patch(
        "/api/me/password",
        json={"current_password": "OldPass1!", "new_password": "NewPass1!"},
        headers=auth,
    )
    assert r.status_code == 204, r.text

    # Old password no longer works
    r = await client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "OldPass1!"},
    )
    assert r.status_code == 401, r.text

    # New password works
    r = await client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "NewPass1!"},
    )
    assert r.status_code == 200, r.text
